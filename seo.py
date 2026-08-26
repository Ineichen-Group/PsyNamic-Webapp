from flask import Response


def register_seo_routes(server):

    @server.route("/robots.txt")
    def robots():
        content = """User-agent: *
Allow: /

Sitemap: https://psynamic.dcr.unibe.ch/sitemap.xml
"""
        return Response(content, mimetype="text/plain")

    @server.route("/sitemap.xml")
    def sitemap():
        urls = [
            "https://psynamic.dcr.unibe.ch/",
            "https://psynamic.dcr.unibe.ch/about",
            "https://psynamic.dcr.unibe.ch/contact",
            "https://psynamic.dcr.unibe.ch/explore/time",
            "https://psynamic.dcr.unibe.ch/explore/search",
            "https://psynamic.dcr.unibe.ch/explore/dual-task",
            "https://psynamic.dcr.unibe.ch/explore/filter",
            "https://psynamic.dcr.unibe.ch/insights/evidence-strength",
            "https://psynamic.dcr.unibe.ch/insights/efficacy-safety",
            "https://psynamic.dcr.unibe.ch/insights/long-term",
            "https://psynamic.dcr.unibe.ch/insights/sex-bias",
            "https://psynamic.dcr.unibe.ch/insights/participants",
            "https://psynamic.dcr.unibe.ch/insights/study-protocol",
            "https://psynamic.dcr.unibe.ch/insights/dosage",
        ]

        xml = '<?xml version="1.0" encoding="UTF-8"?>'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

        for url in urls:
            xml += f"<url><loc>{url}</loc></url>"

        xml += "</urlset>"

        return Response(xml, mimetype="application/xml")
