default_values = {
    'Final Score': 0,
    '*': 0,
}


def get_scoring(assessment):
    scoring_data = assessment.get_score_json()
    pillars_final_scores = {
        '{} Final Score'.format(title): score
        for title, score in scoring_data['final_pillars_score'].items()
    }

    matrix_pillars_scores = {}
    for title, pillars_score in scoring_data['matrix_pillars'].items():
        col_key = '{} Score'.format(title)
        matrix_pillars_scores[col_key] = {}
        for sector, data in pillars_score.items():
            matrix_pillars_scores[col_key][sector] = data['value']

    return {
        'Final Score': scoring_data['final_score'],
        **pillars_final_scores,
        **matrix_pillars_scores,
    }
