from django.db.models import Q
from rest_framework.authtoken.models import Token


def delete_user_auth_token(username):
    """
    Deletes the authentication tokens for the user with the given username

    If no user exists, NO error is returned.
    :param username: Username of the user whose authentication tokens should be deleted
    :return: None
    """
    Token.objects.filter(user__username=username).delete()


def set_user_auth_token(user, key):
    """
    Sets the authentication for the given User.

    Raises an AttributeError if *different* User with the specified key already exists.

    :param user: User whose authentication is being set
    :param key: New authentication key
    :return: None
    """
    # Check that no other user has the same key
    if Token.objects.filter(~Q(user=user), key=key).exists():
        raise AttributeError("The key %s is already in use by another user.", key)

    Token.objects.filter(user=user).delete()
    Token.objects.create(user=user, key=key)

    print "Set API key for user %s to %s" % (user, key)


def matches(answer_one, answer_two):
    """ Check whether two answers match sufficiently for consolidation. """
    return (
        answer_one.question_text == answer_two.question_text and
        answer_one.answer_value_text == answer_two.answer_value_text and
        answer_one.answer_value_numeric == answer_two.answer_value_numeric and
        answer_one.problem_display_name == answer_two.problem_display_name and
        answer_one.correct == answer_two.correct and
        answer_one.value_id == answer_two.value_id
    )


def consolidate_answers(problem):
    """ Attempt to consolidate erroneously randomized answers. """
    for answer in problem:
        answer.consolidated_variant = False

    for i, answer_one in enumerate(problem):
        j = i + 1

        while j < len(problem):
            answer_two = problem[j]

            if matches(answer_one, answer_two):
                answer_one.count += answer_two.count
                answer_one.variant = None
                answer_one.consolidated_variant = True

                problem.remove(answer_two)
            else:
                j += 1

    return problem
