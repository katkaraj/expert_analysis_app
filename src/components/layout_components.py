from dash import html

# vytvoření záhlaví aplikace
header = html.H4(
    "Application for expert analysis",
    className="bg-primary text-white p-3 mb-3 text-center border rounded"
)

# vytvoření zápatí aplikace
footer = html.Footer(
    className="bg-primary p-3 mb-3 text-center border rounded"
)
