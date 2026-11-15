"""F601~F611 기능 테스트. Selenium·GMS는 mock으로 대체한다."""
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import CommentAnalysis
from .services.augment import augment_comments
from .services.summary import summarize_comments


class AugmentTests(SimpleTestCase):
    def test_empty_comments_do_not_call_api(self):
        with patch('stocks.services.augment.run_llm') as mocked:
            self.assertEqual(augment_comments([]), [])
            mocked.assert_not_called()

    @patch('stocks.services.augment.run_llm', return_value='["확장된 첫 댓글", "확장된 둘째 댓글"]')
    def test_augmented_comments_keep_count_and_order(self, mocked):
        result = augment_comments(['첫 댓글', '둘째 댓글'])
        self.assertEqual(result, ['확장된 첫 댓글', '확장된 둘째 댓글'])
        self.assertIn('첫 댓글', mocked.call_args.args[0])

    @patch('stocks.services.augment.run_llm', return_value='["한 문장만"]')
    def test_invalid_number_of_results_raises(self, mocked):
        with self.assertRaises(ValueError):
            augment_comments(['첫 댓글', '둘째 댓글'])

    @patch('stocks.services.augment.run_llm', return_value='["정상", 123]')
    def test_non_string_result_raises(self, mocked):
        with self.assertRaises(ValueError):
            augment_comments(['첫 댓글', '둘째 댓글'])


class SummaryServiceTests(SimpleTestCase):
    def test_empty_does_not_call_api(self):
        with patch('stocks.services.summary.run_llm') as mocked:
            self.assertEqual(summarize_comments([]), '')
            mocked.assert_not_called()

    @patch('stocks.services.summary.run_llm', return_value='  실적 기대와 주가 우려가 공존합니다.  ')
    def test_summarizes_all_raw_comments(self, mocked):
        result = summarize_comments(['실적이 기대됩니다.', '주가가 걱정됩니다.'])
        self.assertEqual(result, '실적 기대와 주가 우려가 공존합니다.')
        prompt = mocked.call_args.args[0]
        self.assertIn('실적이 기대됩니다.', prompt)
        self.assertIn('주가가 걱정됩니다.', prompt)

    @patch('stocks.services.summary.run_llm', return_value=' ')
    def test_blank_response_raises(self, mocked):
        with self.assertRaises(ValueError):
            summarize_comments(['댓글'])


class AnalysisViewTests(TestCase):
    def make_analysis(self, raw=None, summary=''):
        if raw is None:
            raw = ['실적이 좋아 보여요']
        return CommentAnalysis.objects.create(
            keyword='삼성', stock_name='삼성전자', raw_comments=raw,
            cleaned_comments=['실적이 좋아 보여요'] if raw else [],
            augmented_comments=['실적이 긍정적입니다'] if raw else [],
            removed_comments=['부적절한 댓글'] if raw else [],
            iqr_info={'lower': 5, 'upper': 76}, summary=summary,
        )

    def test_empty_company_does_not_start_crawler(self):
        with patch('stocks.views.get_driver') as driver:
            response = self.client.get(reverse('stocks:index'), {'company': '  '})
        self.assertEqual(response.status_code, 200)
        driver.assert_not_called()
        self.assertEqual(CommentAnalysis.objects.count(), 0)

    @patch('stocks.views.augment_comments', return_value=['증강된 문장입니다'])
    @patch('stocks.views.clean_comments', return_value=(['정제된 문장'], {'lower': 5, 'upper': 76}))
    @patch('stocks.views.filter_inappropriate', return_value=(['원본 댓글'], ['제거된 댓글']))
    @patch('stocks.views.collect_comments', return_value=['원본 댓글'])
    @patch('stocks.views.get_stock_name', return_value='삼성전자')
    @patch('stocks.views.get_stock_code', return_value='A005930')
    @patch('stocks.views.search_company')
    @patch('stocks.views.open_main')
    @patch('stocks.views.open_community')
    @patch('stocks.views.get_driver')
    def test_stages_are_saved_and_rendered(
        self, driver, community, main, search, code, name,
        collect, filter_comments, clean, augment,
    ):
        response = self.client.get(reverse('stocks:index'), {'company': '삼성'})
        self.assertEqual(response.status_code, 200)
        driver.return_value.quit.assert_called_once()
        collect.assert_called_once_with(driver.return_value, limit=20)
        augment.assert_called_once_with(['정제된 문장'])
        saved = CommentAnalysis.objects.get()
        self.assertEqual(saved.keyword, '삼성')
        self.assertEqual(saved.raw_comments, ['원본 댓글'])
        self.assertEqual(saved.cleaned_comments, ['정제된 문장'])
        self.assertEqual(saved.augmented_comments, ['증강된 문장입니다'])
        self.assertEqual(saved.removed_comments, ['제거된 댓글'])
        self.assertEqual(saved.summary, '')  # 요약은 버튼 클릭 전까지 생성하지 않음
        self.assertContains(response, 'AI 요약 생성')
        self.assertContains(response, 'DB 저장 완료')

    @patch('stocks.views.augment_comments')
    @patch('stocks.views.filter_inappropriate')
    @patch('stocks.views.collect_comments', return_value=[])
    @patch('stocks.views.get_stock_name', return_value='삼성전자')
    @patch('stocks.views.get_stock_code', return_value='A005930')
    @patch('stocks.views.search_company')
    @patch('stocks.views.open_main')
    @patch('stocks.views.open_community')
    @patch('stocks.views.get_driver')
    def test_no_comments_skips_llm_and_displays_info(
        self, driver, community, main, search, code, name, collect, filter_comments, augment,
    ):
        response = self.client.get(reverse('stocks:index'), {'company': '삼성'})
        self.assertEqual(response.status_code, 200)
        augment.assert_not_called()
        filter_comments.assert_not_called()
        saved = CommentAnalysis.objects.get()
        self.assertEqual(saved.raw_comments, [])
        self.assertContains(response, '수집된 댓글이 없습니다')
        self.assertNotContains(response, 'id="summary-form"')

    @patch('stocks.views.get_stock_code', return_value=None)
    @patch('stocks.views.search_company')
    @patch('stocks.views.open_main')
    @patch('stocks.views.get_driver')
    def test_no_matched_stock_displays_warning(self, driver, main, search, code):
        response = self.client.get(reverse('stocks:index'), {'company': '없는종목'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CommentAnalysis.objects.count(), 0)
        self.assertContains(response, '검색 결과를 찾지 못했습니다')
        driver.return_value.quit.assert_called_once()

    @patch('stocks.views.get_driver', side_effect=RuntimeError('Chrome 실패'))
    def test_browser_failure_is_shown_instead_of_500(self, driver):
        response = self.client.get(reverse('stocks:index'), {'company': '삼성'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CommentAnalysis.objects.count(), 0)
        self.assertContains(response, '데이터를 수집하지 못했습니다')

    @patch('stocks.views.filter_inappropriate', side_effect=RuntimeError('GMS 연결 오류'))
    @patch('stocks.views.collect_comments', return_value=['원본 댓글'])
    @patch('stocks.views.get_stock_name', return_value='삼성전자')
    @patch('stocks.views.get_stock_code', return_value='A005930')
    @patch('stocks.views.search_company')
    @patch('stocks.views.open_main')
    @patch('stocks.views.open_community')
    @patch('stocks.views.get_driver')
    def test_llm_failure_does_not_save_incomplete_result(
        self, driver, community, main, search, code, name, collect, filtr,
    ):
        response = self.client.get(reverse('stocks:index'), {'company': '삼성'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CommentAnalysis.objects.count(), 0)
        self.assertContains(response, 'AI 전처리 또는 증강을 완료하지 못했습니다')
        self.assertContains(response, '원본 댓글')

    @patch('stocks.views.summarize_comments', return_value='긍정과 우려 의견이 공존합니다.')
    @patch('stocks.views.get_driver')
    def test_summary_post_saves_and_redirects_without_recrawling(self, driver, summarize):
        analysis = self.make_analysis()
        response = self.client.post(reverse('stocks:summary', args=[analysis.pk]))
        self.assertRedirects(response, reverse('stocks:analysis-detail', args=[analysis.pk]))
        analysis.refresh_from_db()
        self.assertEqual(analysis.summary, '긍정과 우려 의견이 공존합니다.')
        summarize.assert_called_once_with(analysis.raw_comments)
        driver.assert_not_called()
        detail = self.client.get(reverse('stocks:analysis-detail', args=[analysis.pk]))
        self.assertContains(detail, '긍정과 우려 의견이 공존합니다.')
        self.assertContains(detail, '부적절한 댓글')
        self.assertNotContains(detail, 'id="summary-form"')

    @patch('stocks.views.summarize_comments')
    def test_existing_summary_skips_api(self, summarize):
        analysis = self.make_analysis(summary='기존 요약입니다.')
        response = self.client.post(reverse('stocks:summary', args=[analysis.pk]))
        self.assertEqual(response.status_code, 302)
        summarize.assert_not_called()

    @patch('stocks.views.summarize_comments')
    def test_empty_comments_summary_skips_api(self, summarize):
        analysis = self.make_analysis(raw=[])
        response = self.client.post(reverse('stocks:summary', args=[analysis.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        summarize.assert_not_called()
        self.assertContains(response, '수집된 댓글이 없어 AI 요약을 생성할 수 없습니다')

    @patch('stocks.views.summarize_comments', side_effect=RuntimeError('API 오류'))
    def test_summary_failure_preserves_existing_data(self, summarize):
        analysis = self.make_analysis()
        response = self.client.post(reverse('stocks:summary', args=[analysis.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI 요약을 생성하지 못했습니다')
        analysis.refresh_from_db()
        self.assertEqual(analysis.summary, '')
        self.assertEqual(analysis.raw_comments, ['실적이 좋아 보여요'])

    def test_summary_get_is_not_allowed(self):
        analysis = self.make_analysis()
        response = self.client.get(reverse('stocks:summary', args=[analysis.pk]))
        self.assertEqual(response.status_code, 405)
