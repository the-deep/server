import unittest

from .utils import remove_puncs_and_extra_spaces
from .vector_generator import (
    create_count_vector,
    normalize_count_vector,
    create_trigram_vector,
    EN_TRIGRAMS,
    ES_TRIGRAMS,
    FR_TRIGRAMS,
    InvalidText,
    InvalidLanguage,
    TrigramsNotLoaded,
)

VECTOR_SIZE = 10000


def test_remove_puncs_and_extra_spaces():
    pairs = [
        ('with.punctu!!ation$$', 'with punctu ation'),
        ('$!@#another punctuated te&&xt', 'another punctuated te xt'),
        ('multiple spaces   and  space at the end ', 'multiple spaces and space at the end'),
        ('Mix^^ of CA~`SEs!!', 'mix of ca ses'),
    ]
    for txt, processed in pairs:
        assert remove_puncs_and_extra_spaces(txt) == processed


def test_trigrams_count():
    assert len(EN_TRIGRAMS.keys()) == VECTOR_SIZE, f"{VECTOR_SIZE} trigrams for english"
    assert len(ES_TRIGRAMS.keys()) == VECTOR_SIZE, f"{VECTOR_SIZE} trigrams for spanish"
    assert len(FR_TRIGRAMS.keys()) == VECTOR_SIZE, f"{VECTOR_SIZE} trigrams for french"


class TestVectorCreation(unittest.TestCase):
    """Tests for vector generation"""

    def test_count_vector(self):
        custom_trigrams = {' ab': 0, 'abc': 1, ' bc': 2, 'bc ': 3, ' is': 4, 'is ': 5}
        text = 'Abc is abc. is ab'
        # positions for [' ab', 'abc', ' bc', 'bc ', ' is', 'is ']
        expected_count_vector = [2, 2, 0, 2, 2, 2]
        processed_text = remove_puncs_and_extra_spaces(text)
        vector = create_count_vector(processed_text, custom_trigrams)
        assert len(vector) == len(custom_trigrams.values())
        assert expected_count_vector == vector

    def test_normalize_count_vector(self):
        vector = [1, 2, 3, 4, 5, 5]
        expected_normalized = [0.05, 0.1, 0.15, 0.2, 0.25, 0.25]
        assert normalize_count_vector(vector) == expected_normalized

    def test_create_trigram_vector_invalid_lang(self):
        with self.assertRaises(InvalidLanguage):
            create_trigram_vector('ch', 'test text. does not matter')

    def test_create_trigram_vector_small_document(self):
        with self.assertRaises(InvalidText):
            create_trigram_vector('en', 'te')

        with self.assertRaises(InvalidText):
            create_trigram_vector('fr', '   . ')

        with self.assertRaises(InvalidText):
            create_trigram_vector('es', None)

    def test_create_trigram_vector(self):
        # NOTE: it's infeasible to check exactly the vectors generated
        text = 'Document deduplication for Humanitarian organization!!'
        vector = create_trigram_vector('en', text)
        assert len(vector) == VECTOR_SIZE, f"There should be {VECTOR_SIZE} dimensions"

        assert all(x <= 1 for x in vector), "Every dimension should be <= 1"
        assert any(x > 0 for x in vector), "Some dimension should be > 0"

    def test_different_texts_vectors(self):
        text1 = '''# Major typhoon devastates areas of central Vietnam\n\nKuala Lumpur/Hanoi/Geneva, 29 October, 2020 – A major typhoon has devastated areas of central Vietnam, with dozens of people feared dead in tragic landslides in Quang Nam.\n\nThere are 53 people buried and feared dead in two landslides caused by the storm, according to Vietnam Government authorities and Red Cross teams have been working through the night to help with rescue efforts.\n\nThe storm has worsened floods in areas of central Vietnam and has caused fresh flooding in new areas, including the central highlands near the Laos border.\n\nMadam Nguyen Thi Xuan Thu, Viet Nam Red Cross Society President said: “We are heartbroken by more tragic loss of life as this typhoon has brought further misery and hardships to hundreds of thousands of people in central Vietnam. Around 89,000 homes have roofs blown off, with many destroyed by this storm.”\n\n“Red Cross relief teams are working non-stop to rescue people and provide critical relief as hundreds of thousands of lives have been turned upside down with so many homes and livelihoods devastated in this massive storm.”\n\nInfrastructure has been damaged including electricity and roads, with over 700 communities without power. More food crops and safe drinking water supplies have also been damaged or destroyed in regions of Vietnam already reeling from some of the worst flooding in decades.\n\nNguyen Hung Ha, Bangkok based Program Coordinator, International Federation of Red Cross and Red Crescent Societies, said: “This massive storm is another crippling blow to millions of people already struggling to cope with some of the most dangerous floods on record in central Vietnam.”\n\n“Relief teams are stretched to the limit due to these back-to back storms. We must redouble our efforts to get critical relief supplies, food, drinking water, tarpaulins and blankets to all those who need it in the coming days and weeks,” Mr Nguyen Hung Ha said.\n\nIn response to the existing flooding and impacts as a result of Typhoon Molave, the International Federation of Red Cross and Red Crescent Societies (IFRC) has launched an [Emergency Appeal](https://reliefweb.int/node/3683160) for 3.9 million Swiss Francs to fund relief and recovery efforts for an estimated 160,000 people. IFRC has already provided 500,000 Swiss francs to support local emergency efforts.\n\nIt is estimated that at least 150,000 people are at immediate risk of food shortages and hunger after thousands of hectares of crops have been destroyed, while over 2 million cattle and poultry are dead or swept away in some of the worst flooding in decades.\n\nFor more information or to arrange an interview, contact:\n\nIn Bangkok: Preeti Abraham, +66 61 412 3910, preeti.abraham@ifrc.org\n\nIn Kuala Lumpur: Antony Balmain, +60 12 230 8451, antony.balmain@ifrc.org\n\nIn Geneva: Matthew Cochrane, Mobile +41 79 251 80 39, matthew.cochrane@ifrc.org\n\nAbout IFRC\n\nIFRC is the world’s largest humanitarian network, comprising 192 National Red Cross and Red Crescent Societies working to save lives and promote dignity around the world.[www.ifrc.org](http://www.ifrc.org) \\- Facebook - Twitter - YouTube'''
        text2 = '''# Deadliest shipwreck of the year claims at least 140 lives\n\n*Saint-Louis, Senegal *– At least 140 people have drowned after a vessel carrying around 200 migrants sank off the Senegalese coast, the deadliest shipwreck recorded in 2020.\n\nAccording to media sources, the Senegalese and Spanish navies, and fishermen who were nearby, rescued 59 people and retrieved the remains of 20 others.\n\nThe International Organization for Migration (IOM) is deeply saddened by this recent tragedy, which follows four shipwrecks recorded in the Central Mediterranean last week and another in the UK Channel.\n\n“We call for unity between governments, partners and the international community to dismantle trafficking and smuggling networks that take advantage of desperate youth,” said Bakary Doumbia, IOM Senegal Chief of Mission.\n\n“It is also important that we advocate for enhanced legal channels to undermine the traffickers’ business model and prevent loss of life.”\n\nThe vessel reportedly left Mbour, a coastal town in western Senegal on Saturday (24/10) bound for the Canary Islands, according to local community members. The boat caught fire a few hours after departure and capsized near Saint-Louis, on Senegal’s northwest coast.\n\nThe Government of Senegal and IOM have arranged a mission to travel to Saint- Louis to assess the needs of survivors and provide immediate psychosocial assistance.\n\nThe number of departures from West Africa to the Canary Islands has significantly increased in recent weeks.\n\nIOM Senegal has been monitoring departures from the coast with the assistance of members of the community since the beginning of September. In September alone, [14 boats carrying 663 migrants](https://migration.iom.int/reports/senegal-%E2%80%94-monitoring- movements-canary-islands-%E2%80%94-movements-and-departures- senegal-1%E2%80%9430?close=true) left Senegal for the Canary Islands. Of these departures, 26 per cent were reported to have experienced an incident or shipwreck.\n\nAccording to the Spanish government, 11,006 arrivals have been recorded in the Canary Islands this year compared to 2,557 arrivals during the same period last year. This is still far below peaks seen in 2006 when over 32,000 people arrived.\n\nWith this tragic shipwreck, at least 414 people are known to have died along this route in 2020 according to IOM’s [Missing Migrants Project](https://missingmigrants.iom.int/?utm_source=Unknown+List&utm_campaign=d823a44265-EMAIL_CAMPAIGN_2020_10_29_09_00&utm_medium=email&utm_term=0_-d823a44265-), which recorded 210 fatalities there in all of 2019.\n\n*For more information please contact Aïssatou Sy at IOM's Regional Office for West and Central Africa, Tel: +221 77 479 21 41, Email: aisy@iom.int *'''
        vector1 = create_trigram_vector('en', text1)
        vector2 = create_trigram_vector('en', text2)
        cosine_similarity = sum([x*y for x, y in zip(vector1, vector2)])
        assert vector1 != vector2, "Two vectors should be different"
        assert cosine_similarity != 1, "Cosine similarity should not be 1"
