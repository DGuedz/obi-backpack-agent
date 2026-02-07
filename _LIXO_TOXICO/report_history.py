from feedback_department import FeedbackDepartment

fb = FeedbackDepartment()
# Reportando o erro 500 que ocorreu anteriormente
fb.report_incident(
    component="CoinMarketCap",
    error_code="500",
    message="Internal Server Error: An internal server error occurred.",
    severity="CRITICAL"
)
print("Incidente histórico reportado com sucesso.")
