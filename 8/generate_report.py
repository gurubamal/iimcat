
import re

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

def get_cissp_domain(text):
    text = text.lower()
    if any(keyword in text for keyword in ["password", "authentication", "login", "user", "sudo", "iam"]):
        return "Identity and Access Management (IAM)"
    elif any(keyword in text for keyword in ["firewall", "network", "port", "tcp", "udp", "ssh", "dns", "http", "ssl", "tls"]):
        return "Communication and Network Security"
    elif any(keyword in text for keyword in ["kernel", "hardening", "compiler", "boot", "grub"]):
        return "Security Architecture and Engineering"
    elif any(keyword in text for keyword in ["logging", "auditing", "log", "audit", "syslog", "journald", "accounting"]):
        return "Security Operations"
    elif any(keyword in text for keyword in ["malware", "antivirus", "rootkit"]):
        return "Security Operations"
    elif any(keyword in text for keyword in ["file", "permission", "ownership", "directory", "integrity"]):
        return "Asset Security"
    elif any(keyword in text for keyword in ["vulnerability", "patching", "updates", "software", "package", "repository"]):
        return "Security Operations"
    elif any(keyword in text for keyword in ["development", "compiler", "toolchain"]):
        return "Software Development Security"
    elif any(keyword in text for keyword in ["assessment", "testing", "scan"]):
        return "Security Assessment and Testing"
    elif any(keyword in text for keyword in ["risk", "policy", "compliance", "standard"]):
        return "Security and Risk Management"
    else:
        return "General Security"

def generate_html_report(findings):
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
    <title>Lynis Vulnerability Scan Report</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .domain { margin-top: 2em; }
    </style>
    </head>
    <body>
    <h1>Lynis Vulnerability Scan Report</h1>
    '''

    findings_by_domain = {}
    for finding in findings:
        domain = finding['domain']
        if domain not in findings_by_domain:
            findings_by_domain[domain] = []
        findings_by_domain[domain].append(finding)

    sorted_domains = sorted(findings_by_domain.keys())

    for domain in sorted_domains:
        html += f'<div class="domain"><h2>{domain}</h2>'
        html += "<table><tr><th>Finding</th><th>Suggestion</th></tr>"
        for finding in findings_by_domain[domain]:
            html += f"<tr><td>{finding['finding']}</td><td>{finding['suggestion']}</td></tr>"
        html += "</table></div>"

    html += '''
    </body>
    </html>
    '''
    return html

def main():
    findings = []
    with open('/home/vagrant/Govt/essentials/lynis_scan_report.txt', 'r') as f:
        for line in f:
            clean_line = strip_ansi_codes(line)
            if "[ SUGGESTION ]" in clean_line or "[ WARNING ]" in clean_line:
                finding_type = "Suggestion" if "[ SUGGESTION ]" in clean_line else "Warning"
                finding_text = clean_line.split('[')[0].strip()
                suggestion_text = finding_text
                domain = get_cissp_domain(finding_text)
                findings.append({
                    "finding": f"[{finding_type}] {finding_text}",
                    "suggestion": suggestion_text,
                    "domain": domain
                })

    html_report = generate_html_report(findings)
    with open('/home/vagrant/Govt/essentials/vulnerability_report.html', 'w') as f:
        f.write(html_report)

if __name__ == "__main__":
    main()
