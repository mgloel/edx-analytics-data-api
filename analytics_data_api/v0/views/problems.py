from itertools import groupby

from rest_framework import generics
from rest_framework.exceptions import NotAcceptable

from analytics_data_api.v0.models import ProblemResponseAnswerDistribution
from analytics_data_api.v0.serializers import ProblemResponseAnswerDistributionSerializer, \
    ProblemSubmissionCountSerializer, ConsolidatedAnswerDistributionSerializer
from analytics_data_api.v0.models import GradeDistribution
from analytics_data_api.v0.serializers import GradeDistributionSerializer
from analytics_data_api.v0.models import SequentialOpenDistribution
from analytics_data_api.v0.serializers import SequentialOpenDistributionSerializer
from analytics_data_api.utils import consolidate_answers


class SubmissionCountsListView(generics.ListAPIView):
    """
    Get the number of submissions to one, or more, problems.

    **Example request**

        GET /api/v0/problems/submission_counts/?problem_ids={problem_id},{problem_id}

    **Response Values**

        Returns a collection of counts of total and correct solutions to the specified
        problems. Each collection contains:

            * module_id: The ID of the problem.
            * total: Total number of submissions
            * correct: Total number of *correct* submissions.

    **Parameters**
        problem_ids -- Comma-separated list of problem IDs representing the problems whose data should be returned.
    """

    serializer_class = ProblemSubmissionCountSerializer
    allow_empty = False

    def get_queryset(self):
        problem_ids = self.request.QUERY_PARAMS.get('problem_ids', '')

        if not problem_ids:
            raise NotAcceptable

        problem_ids = problem_ids.split(',')
        queryset = ProblemResponseAnswerDistribution.objects.filter(module_id__in=problem_ids).order_by('module_id')

        data = []

        for problem_id, distribution in groupby(queryset, lambda x: x.module_id):
            total = 0
            correct = 0

            for answer in distribution:
                count = answer.count
                total += count
                if answer.correct:
                    correct += count

            data.append({
                'module_id': problem_id,
                'total': total,
                'correct': correct
            })

        return data


class ProblemResponseAnswerDistributionView(generics.ListAPIView):
    """
    Get the distribution of student answers to a specific problem.

    **Example request**

        GET /api/v0/problems/{problem_id}/answer_distribution

    **Response Values**

        Returns a collection for each unique answer given to specified
        problem. Each collection contains:

            * course_id: The ID of the course for which data is returned.
            * module_id: The ID of the problem.
            * part_id: The ID for the part of the problem. For multi-part
              problems, a collection is returned for each part.
            * correct: Whether the answer was correct (``true``) or not
              (``false``).
            * count: The number of times the answer in this collection was
              given.
            * value_id: The ID of the answer in this collection.
            * answer_value_text: The text of this answer, for text problems.
            * answer_value_numeric: The number for this answer, for numeric
              problems.
            * problem_display_name: The display name for the specified problem.
            * question_text: The question for the specified problem.
            * variant: For randomized problems, the random seed used. If problem
              is not randomized, value is null.
            * created: The date the count was computed.

    **Parameters**

        You can request consolidation of response counts for erroneously randomized problems.

        consolidate -- If True, attempt to consolidate responses, otherwise, do not.

    """

    serializer_class = ProblemResponseAnswerDistributionSerializer
    allow_empty = False

    def get_queryset(self):
        """Select all the answer distribution response having to do with this usage of the problem."""
        problem_id = self.kwargs.get('problem_id')
        consolidate = self.request.QUERY_PARAMS.get('consolidate')

        queryset = ProblemResponseAnswerDistribution.objects.filter(module_id=problem_id).order_by('part_id')
        
        if not consolidate:
            return queryset

        self.serializer_class = ConsolidatedAnswerDistributionSerializer
        consolidated_rows = []

        for part_id, part in groupby(queryset, lambda x: x.part_id):
            consolidated_rows += consolidate_answers([answer for answer in part])

        return consolidated_rows


class GradeDistributionView(generics.ListAPIView):
    """
    Get the distribution of grades for a specific problem.

    **Example request**

        GET /api/v0/problems/{problem_id}/grade_distribution

    **Response Values**

        Returns a collection for each unique grade given to a specified
        problem. Each collection contains:

            * course_id: The ID of the course for which data is returned.
            * module_id: The ID of the problem.
            * grade: The grade being counted in this collection.
            * count: The number of times the grade in this collection was
              given.
            * max_grade: The highest possible grade for this problem.
            * created: The date the count was computed.
    """

    serializer_class = GradeDistributionSerializer
    allow_empty = False

    def get_queryset(self):
        """Select all grade distributions for a particular module"""
        problem_id = self.kwargs.get('problem_id')
        return GradeDistribution.objects.filter(module_id=problem_id)


class SequentialOpenDistributionView(generics.ListAPIView):
    """
    Get the number of views of a subsection, or sequential, in the course.

    **Example request**

        GET /api/v0/problems/{module_id}/sequential_open_distribution

    **Response Values**

        Returns a collection that contains the number of views of the specified
        problem. The collection contains:

            * course_id: The ID of the course for which data is returned.
            * module_id: The ID of the subsection, or sequential.
            * count: The number of times the subsection was viewed.
            * created: The date the count computed.
    """

    serializer_class = SequentialOpenDistributionSerializer
    allow_empty = False

    def get_queryset(self):
        """Select the view count for a specific module"""
        module_id = self.kwargs.get('module_id')
        return SequentialOpenDistribution.objects.filter(module_id=module_id)
