import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.patient_service import map_headers
from agents.matcher_agent import MatcherAgent
from trials.eligibility import EligibilityEngine

def test_patient_normalization():
    headers = ['Patient ID', 'Age', 'Sex', 'Diagnosis', 'IDH Status', 'MGMT Status']
    mapped = map_headers(headers)
    assert mapped['Patient ID'] == 'patient_id'
    assert mapped['Age'] == 'age'
    print('test_patient_normalization PASSED')

def test_age_criterion_yes():
    agent = MatcherAgent()
    patient = {'age': 54}
    result = agent._evaluate_criterion(patient, 'Age >= 18', 'inclusion', 0)
    assert result.status == 'YES'
    print('test_age_criterion_yes PASSED')

def test_age_criterion_no():
    agent = MatcherAgent()
    patient = {'age': 54}
    result = agent._evaluate_criterion(patient, 'Age >= 65', 'inclusion', 0)
    assert result.status == 'NO'
    print('test_age_criterion_no PASSED')

def test_age_criterion_unknown():
    agent = MatcherAgent()
    patient = {'age': None}
    result = agent._evaluate_criterion(patient, 'Age >= 18', 'inclusion', 0)
    assert result.status == 'UNKNOWN'
    print('test_age_criterion_unknown PASSED')

def test_ecog_unknown():
    agent = MatcherAgent()
    patient = {'performance_status': None}
    result = agent._evaluate_criterion(patient, 'ECOG 0-2', 'inclusion', 0)
    assert result.status == 'UNKNOWN'
    print('test_ecog_unknown PASSED')

def test_final_eligibility_eligible():
    engine = EligibilityEngine()
    R = lambda **kw: type('R', (), kw)()
    inclusion = [R(status='YES', criterion='Age >= 18', patient_value=54, reason='ok', evidence_source='test')]
    exclusion = [R(status='NO', criterion='Pregnant', patient_value=False, reason='ok', evidence_source='test')]
    status = engine._determine_final_status(inclusion, exclusion, [])
    assert status == 'ELIGIBLE'
    print('test_final_eligibility_eligible PASSED')

def test_final_eligibility_not_eligible():
    engine = EligibilityEngine()
    R = lambda **kw: type('R', (), kw)()
    inclusion = [R(status='NO', criterion='Age >= 18', patient_value=10, reason='ok', evidence_source='test')]
    status = engine._determine_final_status(inclusion, [], [])
    assert status == 'NOT_ELIGIBLE'
    print('test_final_eligibility_not_eligible PASSED')

def test_final_eligibility_unknown():
    engine = EligibilityEngine()
    R = lambda **kw: type('R', (), kw)()
    inclusion = [
        R(status='YES', criterion='Age >= 18', patient_value=54, reason='ok', evidence_source='test'),
        R(status='UNKNOWN', criterion='ECOG 0-2', patient_value=None, reason='missing', evidence_source='test')
    ]
    status = engine._determine_final_status(inclusion, [], [])
    assert status == 'UNKNOWN'
    print('test_final_eligibility_unknown PASSED')

if __name__ == '__main__':
    test_patient_normalization()
    test_age_criterion_yes()
    test_age_criterion_no()
    test_age_criterion_unknown()
    test_ecog_unknown()
    test_final_eligibility_eligible()
    test_final_eligibility_not_eligible()
    test_final_eligibility_unknown()
    print('All tests passed.')
