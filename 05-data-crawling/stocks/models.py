from django.db import models

# Create your models here.
class CommentAnalysis(models.Model):
    keyword = models.CharField(max_length=100)          # 사용자가 입력한 검색어 (예: 삼성)
    stock_name = models.CharField(max_length=100)       # 실제 매칭된 종목명 (예: 삼성전자)
    raw_comments = models.JSONField(default=list)       # 원본 댓글 목록
    cleaned_comments = models.JSONField(default=list)   # 정제 댓글 목록
    augmented_comments = models.JSONField(default=list) # 증강 댓글 목록
    removed_comments = models.JSONField(default=list)   # 부적절 판단으로 제거된 댓글 (심화 후 화면 복원용)
    iqr_info = models.JSONField(default=dict)           # IQR 임계값 정보 (q1, q3, iqr, lower, upper)
    summary = models.TextField(blank=True)              # 댓글 요약 (심화 F610용, 비워둬도 됨)
    created_at = models.DateTimeField(auto_now_add=True) # 생성 일시

    def __str__(self):
        return f'{self.stock_name} ({self.created_at:%Y-%m-%d %H:%M})'
