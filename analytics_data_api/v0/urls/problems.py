import re

from django.conf.urls import patterns, url

from analytics_data_api.v0.views import problems as views

PROBLEM_URLS = [
    ('answer_distribution', views.ProblemResponseAnswerDistributionView, 'answer_distribution'),
    ('grade_distribution', views.GradeDistributionView, 'grade_distribution'),
]

urlpatterns = patterns(
    '',
    url(r'^submission_counts/$', views.SubmissionCountsListView.as_view(), name='submission_counts'),
    url(r'^(?P<module_id>.+)/sequential_open_distribution/$',
        views.SequentialOpenDistributionView.as_view(), name='sequential_open_distribution'),
)

for path, view, name in PROBLEM_URLS:
    urlpatterns += patterns('', url(r'^(?P<problem_id>.+)/' + re.escape(path) + r'/$', view.as_view(), name=name))
