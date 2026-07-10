from datetime import date

from legalops.triagem import filtrar_candidatos


def _email(sender, subject, data, body):
    return {"sender": sender, "subject": subject, "data": data, "body": body}


def test_tjpr_por_dominio_entra():
    emails = [_email("intimacao@tjpr.jus.br", "Intimação", "2026-07-08", "Projudi ...")]
    out = filtrar_candidatos(emails, janela_dias=7, hoje=date(2026, 7, 10))
    assert len(out) == 1
    assert out[0]["tribunal"] == "tjpr"


def test_newsletter_nao_tribunal_sai():
    emails = [_email("news@migalhas.com.br", "Boletim", "2026-07-09", "notícias jurídicas")]
    out = filtrar_candidatos(emails, janela_dias=7, hoje=date(2026, 7, 10))
    assert out == []


def test_fora_da_janela_sai():
    emails = [_email("intimacao@tjpr.jus.br", "Intimação", "2026-06-01", "Projudi ...")]
    out = filtrar_candidatos(emails, janela_dias=7, hoje=date(2026, 7, 10))
    assert out == []


def test_data_invalida_vai_para_revisao_nao_quebra():
    emails = [_email("intimacao@tjpr.jus.br", "Intimação", "data-ruim", "Projudi ...")]
    out = filtrar_candidatos(emails, janela_dias=7, hoje=date(2026, 7, 10))
    # data ilegível não pode sumir silenciosamente: entra marcado para conferência
    assert len(out) == 1
    assert out[0]["data_suspeita"] is True


def test_detecta_por_header_sem_dominio():
    emails = [_email("noreply@example.com", "Aviso", "2026-07-09", "Sistema Projudi TJPR")]
    out = filtrar_candidatos(emails, janela_dias=7, hoje=date(2026, 7, 10))
    assert len(out) == 1
    assert out[0]["tribunal"] == "tjpr"
