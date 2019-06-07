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

    matrix_pillars_final_scores = scoring_data['matrix_pillars_final_score']

    pillars = {
        pillar: {
            sub_pillar: sp_data['value']
            for sub_pillar, sp_data in pillar_data.items()
        }
        for pillar, pillar_data in scoring_data['pillars'].items()
    }

    matrix_pillars_scores = {}
    for title, pillars_score in scoring_data['matrix_pillars'].items():
        col_key = '{} Score'.format(title)
        matrix_pillars_scores[col_key] = {}
        for sector, data in pillars_score.items():
            matrix_pillars_scores[col_key][sector] = data['value']

    return {
        **pillars,
        **matrix_pillars_scores,
        'final_scores': {
            **pillars_final_scores,
            **matrix_pillars_final_scores,
        },
        '': {
            'Final Score': scoring_data['final_score'],
        }
    }
