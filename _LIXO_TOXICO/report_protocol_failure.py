from feedback_department import FeedbackDepartment

fb = FeedbackDepartment()

print(" Iniciando Reporte de Falha de Protocolo...")

fb.report_incident(
    component="ProfitFlowManager",
    error_code="PROTOCOL_VIOLATION",
    message="ALERTA: Protocolo não executado conforme combinado. Análise técnica falhou (Viés Incorreto) resultando em Drawdown. Ação Corretiva: Modo Resgate Ativado (SL Removido, Gestão Manual para Breakeven).",
    severity="CRITICAL"
)

print(" Incidente registrado no Banco de Reports (system_health.json).")
