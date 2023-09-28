from datetime import datetime, timedelta
from enum import StrEnum
from typing import List
from survey import QuestionBase, Survey


class QuestionKeys(StrEnum):
    Date = 'q_date'
    HadPain = 'q_had_pain'
    FirstNotice = 'q_first_notice'
    WhenStop = 'q_when_stop'
    EyeDellusion = 'q_eye_dellusion'
    WhereHurts = 'q_where_hurts'
    Nature = 'q_nature'
    PhysicalTrigger = 'q_physical_trigger'
    PainIntensity = 'q_pain_intensity'
    HadSickness = 'q_had_sickness'
    HadVomit = 'q_had_vomit'
    LightIrritation = 'q_light_irritation'
    SoundIrritation = 'q_sound_irritation'
    Causes = 'q_causes'
    Painkillers = 'q_painkillers'


QK = QuestionKeys


q_strings = {
    QK.Date: 'Число',
    QK.HadPain: 'Была ли у вас сегодня головная боль?',
    QK.FirstNotice: 'Когда впервые заметили головную боль?',
    QK.WhenStop: 'Когда прекратилась?',
    QK.EyeDellusion: 'В течение часа до начала головной боли отмечали ли Вы зрительные нарушения? (вспышки света, линии-зигзаги, слепые пятна и др.)',
    QK.WhereHurts: 'Где отмечалась головная боль?',
    QK.Nature: 'Характер головной боли',
    QK.PhysicalTrigger: 'Ухудшалась ли головная боль при физической активности? (подъём по лестнице и др.)',
    QK.PainIntensity: 'Какова была в целом интенсивность головной боли?',
    QK.HadSickness: 'Была ли у вас тошнота?',
    QK.HadVomit: 'Была ли рвота?',
    QK.LightIrritation: 'Вас раздражал свет?',
    QK.SoundIrritation: 'Вас раздражал звук?',
    QK.Causes: 'Могло ли что-то послужить причиной головной боли?',
    QK.Painkillers: 'Принимали ли вы сегодня препараты от головной боли? Для каждого препарата укажите название, принятую дозу и время приёма',
}


def validate_date(question: QuestionBase, answer: str) -> bool:
        try:
            datetime.strptime(answer, '%d.%m')
        except ValueError:
            question.note = '\nФормат ввода: дд.мм'
            return False
        
        return True


def suggest_date() -> List[str]:
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    format_ = '%d.%m'
    return [yesterday.strftime(format_), today.strftime(format_)]


def had_pain_next_q(question: QuestionBase, answer: str) -> str:
    return QK.FirstNotice if answer.lower() == 'да' else QK.Painkillers


def build_questions() -> dict[str, QuestionBase]:
    
    yes_no_options = ['Да', 'Нет']

    questions_description = {
        QK.Date: QuestionBase(text=q_strings[QK.Date], next_q=QK.HadPain, 
                              validators=[validate_date], suggestions=suggest_date),

        QK.HadPain: QuestionBase(text=q_strings[QK.HadPain], next_q=had_pain_next_q,
                                 options=yes_no_options),

        QK.FirstNotice: QuestionBase(text=q_strings[QK.FirstNotice], next_q=QK.WhenStop),

        QK.WhenStop: QuestionBase(text=q_strings[QK.WhenStop], next_q=QK.EyeDellusion),

        QK.EyeDellusion: QuestionBase(text=q_strings[QK.EyeDellusion], next_q=QK.WhereHurts,
                                      options=yes_no_options),

        QK.WhereHurts: QuestionBase(text=q_strings[QK.WhereHurts], next_q=QK.Nature, 
                                    options=['С одной стороны', 'С обеих']),

        QK.Nature: QuestionBase(text=q_strings[QK.Nature], next_q=QK.PhysicalTrigger, 
                                options=['Пульсирующая', 'Сжимающая']),

        QK.PhysicalTrigger: QuestionBase(text=q_strings[QK.PhysicalTrigger], 
                                         next_q=QK.PainIntensity, options=yes_no_options),
        
        QK.PainIntensity: QuestionBase(text=q_strings[QK.PainIntensity],
                                       next_q=QK.HadSickness, 
                                       options=['Незначительная', 'Сильная', 'Очень сильная']),

        QK.HadSickness: QuestionBase(text=q_strings[QK.HadSickness], next_q=QK.HadVomit, 
                                     options=['Нет', 'Незначительная', 'Заметная']),

        QK.HadVomit: QuestionBase(text=q_strings[QK.HadVomit], next_q=QK.LightIrritation, 
                                  options=yes_no_options),

        QK.LightIrritation: QuestionBase(text=q_strings[QK.LightIrritation], 
                                         next_q=QK.SoundIrritation, options=yes_no_options),

        QK.SoundIrritation: QuestionBase(text=q_strings[QK.SoundIrritation], next_q=QK.Causes, 
                                         options=yes_no_options),

        QK.Causes: QuestionBase(text=q_strings[QK.Causes], next_q=QK.Painkillers),

        QK.Painkillers: QuestionBase(text=q_strings[QK.Painkillers], next_q=None),
    }

    return questions_description


def get_head_pain_survey():
    return Survey(build_questions(), QK.Date)
