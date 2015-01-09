from django.conf import settings
from rest_framework import serializers

from analytics_data_api.constants import enrollment_modes, genders
from analytics_data_api.v0 import models


# Below are the enrollment modes supported by this API. The audit and honor enrollment modes are merged into honor.
ENROLLMENT_MODES = [enrollment_modes.HONOR, enrollment_modes.PROFESSIONAL, enrollment_modes.VERIFIED]


class CourseActivityByWeekSerializer(serializers.ModelSerializer):
    """
    Representation of CourseActivityByWeek that excludes the id field.

    This table is managed by the data pipeline, and records can be removed and added at any time. The id for a
    particular record is likely to change unexpectedly so we avoid exposing it.
    """

    activity_type = serializers.SerializerMethodField('get_activity_type')

    def get_activity_type(self, obj):
        """
        Lower-case activity type and change active to any.
        """

        activity_type = obj.activity_type.lower()
        if activity_type == 'active':
            activity_type = 'any'

        return activity_type

    class Meta(object):
        model = models.CourseActivityWeekly
        fields = ('interval_start', 'interval_end', 'activity_type', 'count', 'course_id')


class ModelSerializerWithCreatedField(serializers.ModelSerializer):
    created = serializers.DateTimeField(format=settings.DATETIME_FORMAT)


class ProblemSubmissionCountSerializer(serializers.Serializer):
    """
    Serializer for problem submission counts.
    """

    module_id = serializers.CharField()
    total = serializers.IntegerField(default=0)
    correct = serializers.IntegerField(default=0)


class ConsolidatedAnswerDistributionSerializer(serializers.Serializer):
    """
    Serializer for consolidated answer distributions.
    """

    course_id = serializers.CharField(max_length=255)
    module_id = serializers.CharField(max_length=255)
    part_id = serializers.CharField(max_length=255)
    correct = serializers.BooleanField()
    count = serializers.IntegerField()
    value_id = serializers.CharField(max_length=255)
    answer_value_text = serializers.CharField()
    answer_value_numeric = serializers.FloatField()
    variant = serializers.IntegerField()
    consolidated_variant = serializers.BooleanField()
    problem_display_name = serializers.CharField()
    question_text = serializers.CharField()
    created = serializers.DateTimeField()


class ProblemResponseAnswerDistributionSerializer(ModelSerializerWithCreatedField):
    """
    Representation of the Answer Distribution table, without id.

    This table is managed by the data pipeline, and records can be removed and added at any time. The id for a
    particular record is likely to change unexpectedly so we avoid exposing it.
    """

    class Meta(object):
        model = models.ProblemResponseAnswerDistribution
        fields = (
            'course_id',
            'module_id',
            'part_id',
            'correct',
            'count',
            'value_id',
            'answer_value_text',
            'answer_value_numeric',
            'problem_display_name',
            'question_text',
            'variant',
            'created'
        )


class GradeDistributionSerializer(ModelSerializerWithCreatedField):
    """
    Representation of the grade_distribution table without id
    """

    class Meta(object):
        model = models.GradeDistribution
        fields = (
            'module_id',
            'course_id',
            'grade',
            'max_grade',
            'count',
            'created'
        )


class SequentialOpenDistributionSerializer(ModelSerializerWithCreatedField):
    """
    Representation of the sequential_open_distribution table without id
    """

    class Meta(object):
        model = models.SequentialOpenDistribution
        fields = (
            'module_id',
            'course_id',
            'count',
            'created'
        )


class BaseCourseEnrollmentModelSerializer(ModelSerializerWithCreatedField):
    date = serializers.DateField(format=settings.DATE_FORMAT)

    def default_if_none(self, value, default=0):
        return value if value is not None else default


class CourseEnrollmentDailySerializer(BaseCourseEnrollmentModelSerializer):
    """ Representation of course enrollment for a single day and course. """

    class Meta(object):
        model = models.CourseEnrollmentDaily
        fields = ('course_id', 'date', 'count', 'created')


class CourseEnrollmentModeDailySerializer(BaseCourseEnrollmentModelSerializer):
    """ Representation of course enrollment, broken down by mode, for a single day and course. """

    def get_default_fields(self):
        # pylint: disable=super-on-old-class
        fields = super(CourseEnrollmentModeDailySerializer, self).get_default_fields()

        # Create a field for each enrollment mode
        for mode in ENROLLMENT_MODES:
            fields[mode] = serializers.IntegerField(required=True, default=0)

            # Create a transform method for each field
            setattr(self, 'transform_%s' % mode, self._transform_mode)

        return fields

    def _transform_mode(self, _obj, value):
        return self.default_if_none(value, 0)

    class Meta(object):
        model = models.CourseEnrollmentDaily

        # Declare the dynamically-created fields here as well so that they will be picked up by Swagger.
        fields = ['course_id', 'date', 'count', 'created'] + ENROLLMENT_MODES


class CountrySerializer(serializers.Serializer):
    """
    Serialize country to an object with fields for the complete country name
    and the ISO-3166 two- and three-digit codes.

    Some downstream consumers need two-digit codes, others need three. Both are provided to avoid the need
    for conversion.
    """
    alpha2 = serializers.CharField()
    alpha3 = serializers.CharField()
    name = serializers.CharField()


class CourseEnrollmentByCountrySerializer(BaseCourseEnrollmentModelSerializer):
    # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
    country = CountrySerializer(many=False)

    class Meta(object):
        model = models.CourseEnrollmentByCountry
        fields = ('date', 'course_id', 'country', 'count', 'created')


class CourseEnrollmentByGenderSerializer(BaseCourseEnrollmentModelSerializer):
    def get_default_fields(self):
        # pylint: disable=super-on-old-class
        fields = super(CourseEnrollmentByGenderSerializer, self).get_default_fields()

        # Create a field for each gender
        for gender in genders.ALL:
            fields[gender] = serializers.IntegerField(required=True, default=0)

            # Create a transform method for each field
            setattr(self, 'transform_%s' % gender, self._transform_gender)

        return fields

    def _transform_gender(self, _obj, value):
        return self.default_if_none(value, 0)

    class Meta(object):
        model = models.CourseEnrollmentByGender
        fields = ('course_id', 'date', 'female', 'male', 'other', 'unknown', 'created')


class CourseEnrollmentByEducationSerializer(BaseCourseEnrollmentModelSerializer):
    class Meta(object):
        model = models.CourseEnrollmentByEducation
        fields = ('course_id', 'date', 'education_level', 'count', 'created')


class CourseEnrollmentByBirthYearSerializer(BaseCourseEnrollmentModelSerializer):
    class Meta(object):
        model = models.CourseEnrollmentByBirthYear
        fields = ('course_id', 'date', 'birth_year', 'count', 'created')


class CourseActivityWeeklySerializer(serializers.ModelSerializer):
    interval_start = serializers.DateTimeField(format=settings.DATETIME_FORMAT)
    interval_end = serializers.DateTimeField(format=settings.DATETIME_FORMAT)
    any = serializers.IntegerField(required=False)
    attempted_problem = serializers.IntegerField(required=False)
    played_video = serializers.IntegerField(required=False)
    # posted_forum = serializers.IntegerField(required=False)
    created = serializers.DateTimeField(format=settings.DATETIME_FORMAT)

    class Meta(object):
        model = models.CourseActivityWeekly
        # TODO: Add 'posted_forum' here to restore forum data
        fields = ('interval_start', 'interval_end', 'course_id', 'any', 'attempted_problem', 'played_video', 'created')
