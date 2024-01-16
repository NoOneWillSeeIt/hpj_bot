from datetime import datetime, timedelta
from enum import StrEnum
from typing import List, Tuple
from constants import ENTRY_KEY_FORMAT
from survey import Survey, IQuestion, create_question


class Questions(StrEnum):
    Date = 'Число'
    HadPain = 'Была ли у тебя сегодня головная боль?'
    FirstNotice = 'Когда впервые заметил(а) головную боль?'
    WhenStop = 'Когда прекратилась?'
    EyeDellusion = 'В течение часа до начала головной боли отмечал(а) ли ты зрительные нарушения?' \
        ' (вспышки света, линии-зигзаги, слепые пятна и др.)'
    WhereHurts = 'Где отмечалась головная боль?'
    Nature = 'Характер головной боли'
    PhysicalTrigger = 'Ухудшалась ли головная боль при физической активности?' \
        ' (подъём по лестнице и др.)'
    PainIntensity = 'Оцени по 10-балльной шкале интенсивность головной боли'
    HadSickness = 'Была ли у тебя тошнота?'
    HadVomit = 'Была ли рвота?'
    LightIrritation = 'Тебя раздражал свет?'
    SoundIrritation = 'Тебя раздражал звук?'
    Causes = 'Могло ли что-то послужить причиной головной боли?'
    Painkillers = 'Принимал(а) ли ты сегодня препараты от головной боли? ' \
        'Для каждого препарата укажи название, принятую дозу и время приёма'
    Comments = 'Комментарии касательно головной боли сегодня'

    @classmethod
    def to_dict(cls) -> dict:
        return {member.name: member.value for member in cls}


def validate_date(answer: str) -> bool:
    """Check date format is valid"""
    try:
        datetime.strptime(answer, ENTRY_KEY_FORMAT)
    except ValueError:
        return False

    return True


def validate_pain_intensity(answer: str) -> bool:
    """Validate the answer is on a scale of 1 to 10"""
    try:
        num = int(answer)
    except ValueError:
        return False

    return 1 <= num <= 10


def suggest_date() -> List[str]:
    """Suggest today and yesterday to user"""
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    return [yesterday.strftime(ENTRY_KEY_FORMAT), today.strftime(ENTRY_KEY_FORMAT)]


def had_pain_next_q(answer: str) -> str:
    return Questions.FirstNotice if answer.lower() == 'да' else Questions.Painkillers


def build_questions() -> dict[str, IQuestion]:
    """Build questions for survey"""
    yes_no_options = ['Да', 'Нет']

    Q = Questions
    CQ = create_question

    questions_description = {
        Q.Date: CQ(text=Q.Date, next_q=Q.HadPain,
                   validations=[(validate_date, 'Формат ввода: дд.мм')], options=suggest_date(),
                   strict_options=False),

        Q.HadPain: CQ(text=Q.HadPain, next_q=had_pain_next_q, options=yes_no_options),

        Q.FirstNotice: CQ(text=Q.FirstNotice, next_q=Q.WhenStop),

        Q.WhenStop: CQ(text=Q.WhenStop, next_q=Q.EyeDellusion),

        Q.EyeDellusion: CQ(text=Q.EyeDellusion, next_q=Q.WhereHurts, options=yes_no_options),

        Q.WhereHurts: CQ(text=Q.WhereHurts, next_q=Q.Nature),

        Q.Nature: CQ(text=Q.Nature, next_q=Q.PhysicalTrigger,
                     options=['Пульсирующая', 'Сжимающая']),

        Q.PhysicalTrigger: CQ(text=Q.PhysicalTrigger, next_q=Q.PainIntensity,
                              options=yes_no_options),

        Q.PainIntensity: CQ(text=Q.PainIntensity, next_q=Q.HadSickness,
                            validations=[(validate_pain_intensity,
                                          'Нужно ввести число от 1 до 10')],
                            options=list(map(str, range(1, 11)))),

        Q.HadSickness: CQ(text=Q.HadSickness, next_q=Q.HadVomit,
                          options=['Нет', 'Незначительная', 'Заметная']),

        Q.HadVomit: CQ(text=Q.HadVomit, next_q=Q.LightIrritation, options=yes_no_options),

        Q.LightIrritation: CQ(text=Q.LightIrritation, next_q=Q.SoundIrritation,
                              options=yes_no_options),

        Q.SoundIrritation: CQ(text=Q.SoundIrritation, next_q=Q.Causes, options=yes_no_options),

        Q.Causes: CQ(text=Q.Causes, next_q=Q.Painkillers),

        Q.Painkillers: CQ(text=Q.Painkillers, next_q=Q.Comments, options=['Нет'],
                          strict_options=False),

        Q.Comments: CQ(text=Q.Comments, next_q=IQuestion.END, options=['Нет комментариев'],
                       strict_options=False),
    }

    return questions_description


def get_head_pain_survey() -> Survey:
    return Survey(build_questions(), Questions.Date)


def prepare_answers_for_db(replies: dict) -> Tuple[str, dict]:
    """Prepare answers from survey before saving.
    Get rid of StrEnum fields.
    """
    result = {}
    for strenum_key, reply in replies.items():
        result[strenum_key.name] = reply

    return replies[Questions.Date], result
