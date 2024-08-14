import math

sigma_cog = 3
sigma_width = 5
sigma_height = 5
sigma_position = 10
likelihood_position_threshold = 100


def likelihood_cog(cog_detected, cog_ais, time_sec):
    term1 = math.exp(-0.5 * ((cog_detected - cog_ais) / (sigma_cog + 0.2 * time_sec)) ** 2)
    term2 = math.exp(-0.5 * ((cog_detected + 180 - cog_ais) / (sigma_cog + 0.2 * time_sec)) ** 2)
    return term1 + term2


def likelihood_width(width_detected, width_ais):
    return math.exp(-0.5 * ((width_detected - width_ais) / sigma_width) ** 2)


def likelihood_height(height_detected, height_ais):
    return math.exp(-0.5 * ((height_detected - height_ais) / sigma_height) ** 2)


def likelihood_position(position_detected_lat, position_detected_lon, position_ais_lat, position_ais_lon, time_sec):
    distance = math.sqrt(
        (position_ais_lat - position_detected_lat) ** 2 + (position_ais_lon - position_detected_lon) ** 2)
    return math.exp(-0.5 * (distance / (sigma_position + time_sec * 10)) ** 2)


def total_likelihood(likelihood_cog_value, likelihood_width_value, *other_likelihoods):
    result = likelihood_cog_value * likelihood_width_value
    for likelihood in other_likelihoods:
        result *= likelihood
    return result


class Matching_Image:
    def __init__(self):
        pass

    def position_check(self, position_detected_lat, position_detected_lon, position_ais_lat, position_ais_lon,
                       time_sec):
        if likelihood_position(position_detected_lat, position_detected_lon, position_ais_lat, position_ais_lon,
                               time_sec) > likelihood_position_threshold:
            return True
        else:
            return False

    def likelihood(self, cog_detected, cog_ais, width_detected, width_ais, height_detected, height_ais,
                 position_detected_lat, position_detected_lon, position_ais_lat, position_ais_lon, time_sec):
        likelihood_cog_value = likelihood_cog(cog_detected, cog_ais, time_sec)
        likelihood_width_value = likelihood_width(width_detected, width_ais)
        likelihood_height_value = likelihood_height(height_detected, height_ais)
        likelihood_position_value = likelihood_position(position_detected_lat, position_detected_lon,
                                                        position_ais_lat, position_ais_lon, time_sec)
        total_likelihood_value = total_likelihood(likelihood_cog_value, likelihood_width_value,
                                                  likelihood_position_value, likelihood_height_value)
        return total_likelihood_value
