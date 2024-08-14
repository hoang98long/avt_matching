import math

sigma_cog = 3
sigma_width = 5
sigma_position = 10
total_likelihood_threshold = 100


def likelihood_cog(cog_detected, cog_ais, time_sec):
    term1 = math.exp(-0.5 * ((cog_detected - cog_ais) / (sigma_cog + 0.2 * time_sec)) ** 2)
    term2 = math.exp(-0.5 * ((cog_detected + 180 - cog_ais) / (sigma_cog + 0.2 * time_sec)) ** 2)
    return term1 + term2


def likelihood_width(width_detected, width_ais):
    return math.exp(-0.5 * ((width_detected - width_ais) / sigma_width) ** 2)


def likelihood_position(position_detected, position_ais, time_sec):
    distance = position_detected - position_ais
    return math.exp(-0.5 * (distance / (sigma_position + time_sec * 10)) ** 2)


def total_likelihood(likelihood_cog_value, likelihood_width_value, *other_likelihoods):
    result = likelihood_cog_value * likelihood_width_value
    for likelihood in other_likelihoods:
        result *= likelihood
    return result


class Matching_Image:
    def __init__(self):
        pass

    def matching(self, cog_detected, cog_ais, width_detected, width_ais, position_detected, position_ais, time_sec):
        likelihood_cog_value = likelihood_cog(cog_detected, cog_ais, time_sec)
        likelihood_width_value = likelihood_width(width_detected, width_ais)
        likelihood_position_value = likelihood_position(position_detected, position_ais, time_sec)
        total_likelihood_value = total_likelihood(likelihood_cog_value, likelihood_width_value, likelihood_position_value)
        if total_likelihood_value > total_likelihood_threshold:
            return True
        else:
            return False
