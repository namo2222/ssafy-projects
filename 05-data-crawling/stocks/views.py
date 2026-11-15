"""F601~F611: 회사 검색, 댓글 처리, 저장, 요청 시 AI 요약, 예외 안내."""
import logging

from django.contrib import messages
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import CommentAnalysis
from .services.augment import augment_comments
from .services.crawler import (
    get_driver, open_main, search_company, get_stock_code, get_stock_name,
    open_community, collect_comments,
)
from .services.preprocess import CRITERIA, filter_inappropriate, clean_comments
from .services.summary import summarize_comments

logger = logging.getLogger(__name__)


def _context_from_analysis(analysis):
    """저장된 결과에서 화면 표시용 데이터를 만든다."""
    return {
        'company': analysis.keyword,
        'stock_name': analysis.stock_name,
        'raw_comments': analysis.raw_comments,
        'cleaned_comments': analysis.cleaned_comments,
        'augmented_comments': analysis.augmented_comments,
        'removed_comments': analysis.removed_comments,
        'iqr_info': analysis.iqr_info,
        'analysis': analysis,
    }


def index(request):
    """회사명 입력 → 크롤링 → 정제 → 증강 → 저장. 예외 시 안전하게 안내한다."""
    company = request.GET.get('company', '').strip()

    # F601: 빈 입력이면 크롤링 및 API를 호출하지 않는다.
    if not company:
        return render(request, 'stocks/index.html')

    context = {
        'company': company,
        'stock_name': None,
        'raw_comments': [],
        'removed_comments': [],
        'cleaned_comments': [],
        'augmented_comments': [],
        'iqr_info': {},
        'analysis': None,
    }
    print(f'입력된 회사명: {company}')

    # F603~F604: 드라이버 생성 실패, 연결 실패, 화면 구조 변경도 안내.
    driver = None
    try:
        driver = get_driver()
        open_main(driver)
        search_company(driver, company)
        stock_code = get_stock_code(driver)
        if not stock_code:
            messages.warning(
                request,
                '검색 결과를 찾지 못했습니다. 회사명을 확인해 주세요. '
                '토스증권 화면이 변경된 경우에도 검색에 실패할 수 있습니다.',
            )
            return render(request, 'stocks/index.html', context)

        context['stock_name'] = get_stock_name(driver)
        open_community(driver, stock_code)
        context['raw_comments'] = collect_comments(driver, limit=20)
    except Exception:
        logger.exception('토스증권 검색/댓글 수집에 실패했습니다. 검색어=%r', company)
        messages.error(
            request,
            '토스증권에서 데이터를 수집하지 못했습니다. '
            '인터넷 연결이나 사이트 화면을 확인하고 다시 시도해 주세요.',
        )
        return render(request, 'stocks/index.html', context)
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                logger.warning('크롬 드라이버 종료에 실패했습니다.', exc_info=True)

    raw_comments = context['raw_comments']
    if not raw_comments:
        # F611: 댓글이 없는 상황도 처리하고 불필요한 LLM 호출을 건너뛴다.
        messages.info(
            request,
            '해당 종목에서 수집된 댓글이 없습니다. '
            '실제로 댓글이 없거나, 토스증권 화면 구조가 바뀌었을 수 있습니다.',
        )
    else:
        # F605~F606: API 오류 시 500 에러를 보여주지 않고 수집된 데이터만 화면에 표시.
        try:
            kept, context['removed_comments'] = filter_inappropriate(
                raw_comments, CRITERIA['strict']
            )
            context['cleaned_comments'], context['iqr_info'] = clean_comments(kept)
            cleaned = context['cleaned_comments']
            context['augmented_comments'] = augment_comments(cleaned) if cleaned else []
        except Exception:
            logger.exception('GMS 전처리/증강에 실패했습니다. 검색어=%r', company)
            messages.error(
                request,
                '댓글은 수집했지만 AI 전처리 또는 증강을 완료하지 못했습니다. '
                'GMS API 설정이나 연결을 확인하고 다시 분석해 주세요. '
                '미완성 결과는 DB에 저장하지 않았습니다.',
            )
            return render(request, 'stocks/index.html', context)

    # F602/F607: 모든 필수 처리 과정이 성공한 경우에만 통합 저장.
    try:
        analysis = CommentAnalysis.objects.create(
            keyword=company,
            stock_name=context['stock_name'],
            raw_comments=raw_comments,
            cleaned_comments=context['cleaned_comments'],
            augmented_comments=context['augmented_comments'],
            removed_comments=context['removed_comments'],
            iqr_info=context['iqr_info'],
        )
    except DatabaseError:
        logger.exception('분석 결과 DB 저장에 실패했습니다. 검색어=%r', company)
        messages.error(request, '분석은 완료했지만 DB에 저장하지 못했습니다. DB 설정을 확인해 주세요.')
        return render(request, 'stocks/index.html', context)

    context['analysis'] = analysis
    print(
        f'[DB 저장] ID={analysis.pk}, 종목명={analysis.stock_name}: '
        f'원본 {len(raw_comments)}개 → 정제 {len(analysis.cleaned_comments)}개 '
        f'→ 증강 {len(analysis.augmented_comments)}개'
    )
    return render(request, 'stocks/index.html', context)


def analysis_detail(request, pk):
    """F610: 요약 후 재크롤링하지 않고 기존 DB 분석을 보여주는 GET 화면."""
    analysis = get_object_or_404(CommentAnalysis, pk=pk)
    return render(request, 'stocks/index.html', _context_from_analysis(analysis))


@require_POST
def summarize_analysis(request, pk):
    """F610: 요약 버튼 클릭 시에만 GMS API를 1회 호출한다."""
    analysis = get_object_or_404(CommentAnalysis, pk=pk)

    if analysis.summary.strip():
        messages.info(request, '이미 생성된 AI 요약을 표시합니다.')
    elif not analysis.raw_comments:
        messages.warning(request, '수집된 댓글이 없어 AI 요약을 생성할 수 없습니다.')
    else:
        try:
            analysis.summary = summarize_comments(analysis.raw_comments)
            if not analysis.summary.strip():
                raise ValueError('요약 결과가 비어 있습니다.')
            analysis.save(update_fields=['summary'])
            messages.success(request, '수집한 댓글의 AI 요약이 생성되어 DB에 저장되었습니다.')
        except Exception:
            logger.exception('AI 요약에 실패했습니다. 분석 ID=%s', analysis.pk)
            messages.error(
                request,
                'AI 요약을 생성하지 못했습니다. GMS API 연결과 설정을 확인한 뒤 다시 시도해 주세요. '
                '기존 댓글 분석 결과는 그대로 보존됩니다.',
            )

    return redirect('stocks:analysis-detail', pk=analysis.pk)
