from pathlib import Path
from core.router import Dispatcher

ROOT = Path(__file__).resolve().parent
D = Dispatcher(ROOT)

assert D.plan("Проанализируй голубые фишки и сделай портфель")['skills'][0] == 'russian-investment-analysis'
assert '1c-ut-documents' in D.plan("Распознай счет-фактуру для УТ 8.3")['skills']
assert 'grants-and-project-applications' in D.plan("Подготовь грантовую заявку")['skills']
print('OK: dispatcher routing tests passed')
