import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MCP_ENDPOINT = "https://www.openaccountants.com/api/mcp"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/openaccountants/openaccountants/main/skills"
CACHE_DIR = Path("data") / "openaccountants"

TURKIYE_FALLBACK_SKILLS = {
    "tr-income-tax-2025": {
        "title": "Gelir Vergisi Dilimleri 2025",
        "slug": "tr-income-tax-2025",
        "jurisdiction": "TR",
        "category": "income-tax",
        "description": "2025 yili gelir vergisi tarifesi - ücretli ve diger kazanc türleri",
        "rates": [
            {"min": 0, "max": 110000, "rate": 0.15, "label": "%15"},
            {"min": 110000, "max": 230000, "rate": 0.20, "label": "%20", "excess": 110000},
            {"min": 230000, "max": 580000, "rate": 0.27, "label": "%27", "excess": 230000},
            {"min": 580000, "max": 3000000, "rate": 0.35, "label": "%35", "excess": 580000},
            {"min": 3000000, "max": None, "rate": 0.40, "label": "%40", "excess": 3000000},
        ],
    },
    "tr-vat-2025": {
        "title": "KDV Oranlari 2025",
        "slug": "tr-vat-2025",
        "jurisdiction": "TR",
        "category": "vat",
        "description": "Katma Deger Vergisi oranlari",
        "rates": [
            {"rate": 0.01, "label": "%1", "scope": "Temel gida, kitap, gazete gibi indirimli ürünler"},
            {"rate": 0.10, "label": "%10", "scope": "Tekstil, mobilya, beyaz esya gibi ürünler"},
            {"rate": 0.20, "label": "%20", "scope": "Genel oran - çogu mal ve hizmet"},
        ],
    },
    "tr-corporate-tax-2025": {
        "title": "Kurumlar Vergisi 2025",
        "slug": "tr-corporate-tax-2025",
        "jurisdiction": "TR",
        "category": "corporate-tax",
        "description": "Kurumlar Vergisi orani",
        "rates": [
            {"rate": 0.25, "label": "%25", "scope": "Genel kurumlar vergisi orani"},
            {"rate": 0.10, "label": "%10", "scope": "Ihracat kazanc indirimi sonrasi fiili oran"},
            {"rate": 0.01, "label": "%1", "scope": "Halka açik sirketlerde indirimli oran (pay oranina göre)"},
        ],
    },
    "tr-payroll-sgk-2025": {
        "title": "SGK Prim Oranlari 2025",
        "slug": "tr-payroll-sgk-2025",
        "jurisdiction": "TR",
        "category": "payroll",
        "description": "Sosyal Güvenlik Kurumu prim oranlari",
        "rates": [
            {"rate": 0.14, "label": "%14", "scope": "SGK Isci primi (çalisan)"},
            {"rate": 0.075, "label": "%7.5", "scope": "SGK Isveren primi (isveren)"},
            {"rate": 0.02, "label": "%2", "scope": "Isveren issizlik sigorta primi"},
            {"rate": 0.01, "label": "%1", "scope": "Çalisan issizlik sigorta primi"},
            {"rate": 0.002, "label": "%0.2", "scope": "Damga vergisi (brüt ücret üzerinden)"},
        ],
    },
    "tr-bookkeeping-standards": {
        "title": "Tek Düzen Hesap Plani - Muhasebe Standartlari",
        "slug": "tr-bookkeeping-standards",
        "jurisdiction": "TR",
        "category": "bookkeeping",
        "description": "Türkiye Tek Düzen Hesap Plani ve muhasebe standartlari",
        "rules": [
            "Tek Düzen Hesap Plani (TDHP) 1-9 arasi ana hesap gruplarindan olsur",
            "1-li Hesap Grubu: Dönen Varliklar",
            "2-li Hesap Grubu: Duran Varliklar",
            "3-li Hesap Grubu: Kisa Vadeli Yabanci Kaynaklar",
            "4-li Hesap Grubu: Uzun Vadeli Yabanci Kaynaklar",
            "5-li Hesap Grubu: Öz Kaynaklar",
            "6-li Hesap Grubu: Gelir Tablosu Hesaplari",
            "7-li Hesap Grubu: Maliyet Hesaplari",
            "8-li Hesap Grubu: (Bos - ileride kullanilmak üzere)",
            "9-li Hesap Grubu: Nazim Hesaplar",
            "TFRS/TMS standartlarina uyum zorunludur",
            "Yillik enflasyon muhasebesi uygulamasi (2024 itibariyle yeniden zorunlu)",
        ],
    },
}

TURKIYE_WITHHOLDING_RATES = {
    "dividend": 0.15,
    "interest": 0.10,
    "rental": 0.20,
    "freelance": 0.20,
    "real-estate-sale": 0.20,
}


class OpenAccountantsAdapter:
    """OpenAccountants entegrasyonu - vergi ve muhasebe kurallari"""

    def __init__(self, cache_dir=None):
        self._skills_cache = {}
        self._cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_tax_skills(self, jurisdiction="TR", category=None):
        skills = self._fetch_skills(jurisdiction)
        if category:
            return [s for s in skills if s.get("category") == category]
        return skills

    def get_vat_rules(self, jurisdiction="TR"):
        return self._get_skill_by_slug(f"{jurisdiction.lower()}-vat-2025") or self._get_skill_by_slug(
            f"{jurisdiction.lower()}-vat"
        )

    def get_income_tax_rules(self, jurisdiction="TR"):
        return self._get_skill_by_slug(f"{jurisdiction.lower()}-income-tax-2025") or self._get_skill_by_slug(
            f"{jurisdiction.lower()}-income-tax"
        )

    def get_payroll_rules(self, jurisdiction="TR"):
        return self._get_skill_by_slug(f"{jurisdiction.lower()}-payroll-sgk-2025") or self._get_skill_by_slug(
            f"{jurisdiction.lower()}-payroll"
        )

    def get_bookkeeping_standards(self, jurisdiction="TR"):
        return self._get_skill_by_slug(f"{jurisdiction.lower()}-bookkeeping-standards") or self._get_skill_by_slug(
            f"{jurisdiction.lower()}-bookkeeping"
        )

    def apply_skill(self, skill_slug, scenario_data):
        skill = self._get_skill_by_slug(skill_slug)
        if not skill:
            raise ValueError(f"Skill '{skill_slug}' not found")
        return self._compute(skill, scenario_data)

    def search_skills(self, query, jurisdiction=None):
        results = []
        for j in ([jurisdiction] if jurisdiction else self._known_jurisdictions()):
            for skill in self._fetch_skills(j):
                if query.lower() in skill.get("title", "").lower() or query.lower() in skill.get("description", "").lower():
                    results.append(skill)
        return results

    def format_tax_advice(self, skill_data):
        return self._format_advice(skill_data)

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    def _fetch_skills(self, jurisdiction):
        j = jurisdiction.upper()
        if j in self._skills_cache:
            return self._skills_cache[j]

        skills = self._try_mcp(j)
        if skills is None:
            skills = self._try_github_raw(j)
        if skills is None:
            skills = self._try_cache(j)
        if skills is None:
            skills = self._fallback(j)

        if skills is None:
            skills = []
        self._skills_cache[j] = skills
        self._save_cache(j, skills)
        return skills

    def _try_mcp(self, jurisdiction):
        try:
            payload = json.dumps({
                "jsonrpc": "2.0",
                "method": "skills/list",
                "params": {"jurisdiction": jurisdiction},
                "id": 1,
            }).encode("utf-8")
            req = urllib.request.Request(
                MCP_ENDPOINT,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return self._normalise_skills(data.get("result", []), jurisdiction)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
            return None

    def _try_github_raw(self, jurisdiction):
        url = f"{GITHUB_RAW_BASE}/{jurisdiction}/"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
            files = self._parse_github_listing(content)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return None

        skills = []
        for fname in files:
            if fname.endswith(".md"):
                skill = self._fetch_and_parse_md(jurisdiction, fname)
                if skill:
                    skills.append(skill)
        return skills if skills else None

    def _try_cache(self, jurisdiction):
        cache_path = self._cache_dir / f"{jurisdiction.upper()}.json"
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _fallback(self, jurisdiction):
        if jurisdiction.upper() == "TR":
            return list(TURKIYE_FALLBACK_SKILLS.values())
        return None

    # ------------------------------------------------------------------
    # Markdown parsing
    # ------------------------------------------------------------------

    def _fetch_and_parse_md(self, jurisdiction, fname):
        url = f"{GITHUB_RAW_BASE}/{jurisdiction}/{fname}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                md = resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            return None
        return self._parse_md(md, jurisdiction)

    def _parse_md(self, md, jurisdiction):
        lines = md.splitlines()
        slug_match = re.search(r"slug:\s*(.+)", md)
        title_match = re.search(r"^#\s+(.+)", md, re.MULTILINE)
        cat_match = re.search(r"category:\s*(.+)", md)

        skill = {
            "slug": slug_match.group(1).strip() if slug_match else None,
            "title": title_match.group(1).strip() if title_match else "Untitled",
            "jurisdiction": jurisdiction.upper(),
            "category": cat_match.group(1).strip() if cat_match else "general",
            "description": "",
            "rates": [],
            "rules": [],
        }

        desc_lines = []
        in_rates = False
        in_rules = False
        for line in lines:
            if line.startswith("## Rates"):
                in_rates = True
                in_rules = False
                continue
            if line.startswith("## Rules"):
                in_rates = False
                in_rules = True
                continue
            if line.startswith("##"):
                in_rates = False
                in_rules = False
                continue

            if in_rates:
                rate_match = re.match(r"\|?\s*([\d.]+%?)\s*\|?\s*(.*)", line)
                if rate_match:
                    raw = rate_match.group(1).strip().replace("%", "")
                    try:
                        rate_val = float(raw) / 100 if "%" not in rate_match.group(1) else float(raw) / 100
                    except ValueError:
                        continue
                    skill["rates"].append({
                        "rate": rate_val,
                        "label": rate_match.group(1).strip(),
                        "scope": rate_match.group(2).strip() if rate_match.group(2).strip() else "",
                    })
            elif in_rules:
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    skill["rules"].append(line.strip().lstrip("-*").strip())
            else:
                if line.strip() and not line.startswith("#") and not line.startswith("---"):
                    desc_lines.append(line.strip())

        skill["description"] = " ".join(desc_lines)
        return skill if skill["slug"] else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_skill_by_slug(self, slug):
        for j in self._known_jurisdictions():
            for skill in self._fetch_skills(j):
                if skill.get("slug") == slug:
                    return skill
        return None

    def _known_jurisdictions(self):
        cached = list(self._skills_cache.keys())
        return cached if cached else ["TR"]

    def _normalise_skills(self, raw_list, jurisdiction):
        normalised = []
        for item in raw_list:
            if isinstance(item, dict):
                item.setdefault("jurisdiction", jurisdiction.upper())
                item.setdefault("category", "general")
                item.setdefault("rates", [])
                item.setdefault("rules", [])
                normalised.append(item)
        return normalised

    def _parse_github_listing(self, html):
        files = re.findall(r'href="([^"]+\.md)"', html)
        return [f.split("/")[-1] for f in files]

    def _save_cache(self, jurisdiction, skills):
        cache_path = self._cache_dir / f"{jurisdiction.upper()}.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Computation
    # ------------------------------------------------------------------

    def _compute(self, skill, scenario_data):
        rates = skill.get("rates", [])
        if not rates:
            return {"result": None, "explanation": "No rate data available in skill"}

        amount = scenario_data.get("amount", 0)
        currency = scenario_data.get("currency", "TRY")

        if skill.get("category") == "income-tax":
            return self._compute_income_tax(rates, amount, currency)
        if skill.get("category") == "vat":
            return self._compute_vat(rates, amount, currency)
        if skill.get("category") == "payroll":
            return self._compute_payroll(rates, amount, currency)
        if skill.get("category") == "corporate-tax":
            return self._compute_flat_rate(rates, amount, currency)

        return {"result": round(amount * (rates[0]["rate"]), 2), "currency": currency, "applied_rate": rates[0]["label"]}

    def _compute_income_tax(self, rates, amount, currency):
        tax = 0.0
        brackets = sorted(rates, key=lambda r: r.get("min", 0))
        breakdown = []
        for bracket in brackets:
            b_min = bracket.get("min", 0)
            b_max = bracket.get("max")
            rate = bracket.get("rate", 0)
            if amount > b_min:
                taxable = min(amount, b_max) - b_min if b_max else amount - b_min
                taxable = max(taxable, 0)
                bracket_tax = round(taxable * rate, 2)
                tax += bracket_tax
                breakdown.append({
                    "bracket": bracket["label"],
                    "taxable": round(taxable, 2),
                    "tax": bracket_tax,
                })
        total_tax = round(tax, 2)
        effective = round((total_tax / amount * 100), 2) if amount else 0
        return {
            "result": total_tax,
            "currency": currency,
            "effective_rate": f"%{effective}",
            "breakdown": breakdown,
            "explanation": f"{amount:,.2f} {currency} üzerinden {total_tax:,.2f} {currency} gelir vergisi hesaplandi (efektif %{effective}).",
        }

    def _compute_vat(self, rates, amount, currency):
        return self._compute_flat_rate(rates, amount, currency)

    def _compute_payroll(self, rates, amount, currency):
        deductions = []
        total_deductions = 0.0
        for rate_item in rates:
            deduction = round(amount * rate_item["rate"], 2)
            total_deductions += deduction
            deductions.append({
                "label": rate_item["label"],
                "scope": rate_item.get("scope", ""),
                "amount": deduction,
            })
        net = round(amount - total_deductions, 2)
        return {
            "result": net,
            "gross": amount,
            "total_deductions": round(total_deductions, 2),
            "currency": currency,
            "deductions": deductions,
            "explanation": (
                f"{amount:,.2f} {currency} brüt ücretten {total_deductions:,.2f} {currency} "
                f"kesinti yapilmistir. Net: {net:,.2f} {currency}."
            ),
        }

    def _compute_flat_rate(self, rates, amount, currency):
        rate = rates[0]["rate"]
        computed = round(amount * rate, 2)
        return {
            "result": computed,
            "currency": currency,
            "applied_rate": rates[0]["label"],
            "explanation": f"{amount:,.2f} {currency} × {rates[0]['label']} = {computed:,.2f} {currency}.",
        }

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_advice(skill_data):
        lines = []
        lines.append(f"## {skill_data.get('title', 'Vergi Bilgisi')}")
        lines.append("")
        if skill_data.get("description"):
            lines.append(skill_data["description"])
            lines.append("")

        rates = skill_data.get("rates", [])
        if rates:
            lines.append("### Oranlar")
            for r in rates:
                scope = f" - {r.get('scope', '')}" if r.get("scope") else ""
                lines.append(f"- **{r.get('label', '')}**{scope}")
            lines.append("")

        rules = skill_data.get("rules", [])
        if rules:
            lines.append("### Kurallar")
            for rule in rules:
                lines.append(f"- {rule}")
            lines.append("")

        withholding = skill_data.get("withholding_rates")
        if withholding:
            lines.append("### Stopaj Oranlari")
            for k, v in withholding.items():
                lines.append(f"- **{k.replace('-', ' ').title()}**: %{v*100:.0f}")
            lines.append("")

        return "\n".join(lines)
