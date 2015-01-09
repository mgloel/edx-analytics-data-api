# coding=utf-8
# NOTE: Full URLs are used throughout these tests to ensure that the API contract is fulfilled. The URLs should *not*
# change for versions greater than 1.0.0. Tests target a specific version of the API, additional tests should be added
# for subsequent versions if there are breaking changes introduced in those versions.

# pylint: disable=no-member,no-value-for-parameter

from django_dynamic_fixture import G

from analytics_data_api.v0 import models
from analytics_data_api.v0.serializers import ProblemResponseAnswerDistributionSerializer, \
    GradeDistributionSerializer, SequentialOpenDistributionSerializer
from analytics_data_api.v0.tests.views import DemoCourseMixin
from analyticsdataserver.tests import TestCaseWithAuthentication


class AnswerDistributionTests(TestCaseWithAuthentication):
    path = '/answer_distribution/'
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.course_id = "org/num/run"
        cls.module_id = "i4x://org/num/run/problem/RANDOMNUMBER"
        cls.part_id = "i4x-org-num-run-problem-RANDOMNUMBER_2_1"
        cls.correct = True
        cls.value_id = '3'
        cls.answer_value_text = '3'
        cls.answer_value_numeric = 3.0
        cls.problem_display_name = 'Test Problem'
        cls.question_text = 'Question Text'

        cls.ad1 = G(
            models.ProblemResponseAnswerDistribution,
            course_id=cls.course_id,
            module_id=cls.module_id,
            part_id=cls.part_id,
            correct=cls.correct,
            value_id=cls.value_id,
            answer_value_text=cls.answer_value_text,
            answer_value_numeric=cls.answer_value_numeric,
            problem_display_name=cls.problem_display_name,
            question_text=cls.question_text,
            variant=123,
            count=1
        )
        cls.ad2 = G(
            models.ProblemResponseAnswerDistribution,
            course_id=cls.course_id,
            module_id=cls.module_id,
            part_id=cls.part_id,
            correct=cls.correct,
            value_id=cls.value_id,
            answer_value_text=cls.answer_value_text,
            answer_value_numeric=cls.answer_value_numeric,
            problem_display_name=cls.problem_display_name,
            question_text=cls.question_text,
            variant=345,
            count=2
        )
        cls.ad3 = G(
            models.ProblemResponseAnswerDistribution,
            course_id=cls.course_id,
            module_id=cls.module_id,
            part_id=cls.part_id,
        )

    def test_get(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % (self.module_id, self.path))
        self.assertEquals(response.status_code, 200)

        expected_data = models.ProblemResponseAnswerDistribution.objects.filter(module_id=self.module_id)
        expected_data = [ProblemResponseAnswerDistributionSerializer(answer).data for answer in expected_data]
        self.assertEqual(response.data, expected_data)

    def test_consolidated_get(self):
        response = self.authenticated_get(
            '/api/v0/problems/{0}{1}?consolidate={2}'.format(self.module_id, self.path, True))
        self.assertEquals(response.status_code, 200)

        expected_data = [
            ProblemResponseAnswerDistributionSerializer(self.ad1).data,
            ProblemResponseAnswerDistributionSerializer(self.ad3).data,
        ]
        expected_data[0]['count'] += self.ad2.count
        expected_data[0]['variant'] = None
        expected_data[0]['consolidated_variant'] = True

        expected_data[1]['consolidated_variant'] = False

        self.assertEquals(response.data, expected_data)

    def test_get_404(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % ("DOES-NOT-EXIST", self.path))
        self.assertEquals(response.status_code, 404)


class GradeDistributionTests(TestCaseWithAuthentication):
    path = '/grade_distribution/'
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.course_id = "org/class/test"
        cls.module_id = "i4x://org/class/test/problem/RANDOM_NUMBER"
        cls.ad1 = G(
            models.GradeDistribution,
            course_id=cls.course_id,
            module_id=cls.module_id,
        )

    def test_get(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % (self.module_id, self.path))
        self.assertEquals(response.status_code, 200)

        expected_dict = GradeDistributionSerializer(self.ad1).data
        actual_list = response.data
        self.assertEquals(len(actual_list), 1)
        self.assertDictEqual(actual_list[0], expected_dict)

    def test_get_404(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % ("DOES-NOT-EXIST", self.path))
        self.assertEquals(response.status_code, 404)


class SequentialOpenDistributionTests(TestCaseWithAuthentication):
    path = '/sequential_open_distribution/'
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.course_id = "org/class/test"
        cls.module_id = "i4x://org/class/test/problem/RANDOM_NUMBER"
        cls.ad1 = G(
            models.SequentialOpenDistribution,
            course_id=cls.course_id,
            module_id=cls.module_id,
        )

    def test_get(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % (self.module_id, self.path))
        self.assertEquals(response.status_code, 200)

        expected_dict = SequentialOpenDistributionSerializer(self.ad1).data
        actual_list = response.data
        self.assertEquals(len(actual_list), 1)
        self.assertDictEqual(actual_list[0], expected_dict)

    def test_get_404(self):
        response = self.authenticated_get('/api/v0/problems/%s%s' % ("DOES-NOT-EXIST", self.path))
        self.assertEquals(response.status_code, 404)


class SubmissionCountsListViewTests(DemoCourseMixin, TestCaseWithAuthentication):
    path = '/api/v0/problems/submission_counts/'

    @classmethod
    def setUpClass(cls):
        super(SubmissionCountsListViewTests, cls).setUpClass()
        cls.ad_1 = G(models.ProblemResponseAnswerDistribution)
        cls.ad_2 = G(models.ProblemResponseAnswerDistribution)

    def _get_data(self, problem_ids=None):
        """
        Retrieve data for the specified problems from the server.
        """

        url = self.path

        if problem_ids:
            problem_ids = ','.join(problem_ids)
            url = '{}?problem_ids={}'.format(url, problem_ids)

        return self.authenticated_get(url)

    def assertValidResponse(self, *problem_ids):
        expected_data = []
        for problem_id in problem_ids:
            _models = models.ProblemResponseAnswerDistribution.objects.filter(module_id=problem_id)
            serialized = [{'module_id': model.module_id, 'total': model.count, 'correct': model.correct or 0} for model
                          in _models]
            expected_data += serialized

        response = self._get_data(problem_ids)
        self.assertEquals(response.status_code, 200)

        actual = response.data
        self.assertListEqual(actual, expected_data)

    def test_get(self):
        """
        The view should return data when data exists for at least one of the problems.
        """

        problem_id_1 = self.ad_1.module_id
        problem_id_2 = self.ad_2.module_id

        self.assertValidResponse(problem_id_1)
        self.assertValidResponse(problem_id_1, problem_id_2)
        self.assertValidResponse(problem_id_1, problem_id_2, 'DOES-NOT-EXIST')

    def test_get_404(self):
        """
        The view should return 404 if data does not exist for at least one of the provided problems.
        """

        problem_ids = ['DOES-NOT-EXIST']
        response = self._get_data(problem_ids)
        self.assertEquals(response.status_code, 404)

    def test_get_406(self):
        """
        The view should return a 406 if no problem ID values are supplied.
        """
        response = self._get_data()
        self.assertEquals(response.status_code, 406)
