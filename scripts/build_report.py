"""Build the final assignment report as a Word document."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "report" / "figures"
OUT = ROOT / "report" / "Zadanie1_Report.docx"


def set_run_font(run, *, bold=False, italic=False, size=11):
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")


def add_para(doc, text, *, bold=False, italic=False, size=11, align="justify",
             space_after=6, space_before=0, first_line=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if first_line and align == "justify":
        pf.first_line_indent = Cm(0.75)
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "left":
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run_font(run, bold=bold, italic=italic, size=size)
    return p


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(run, bold=True, size=14 if level == 1 else 12)
    h.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    return h


def add_caption(doc, text):
    return add_para(doc, text, italic=True, size=10, align="center",
                    space_before=4, space_after=10, first_line=False)


def add_figure(doc, path: Path, width_cm=12.0, caption: str = ""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        add_caption(doc, caption)


def add_table(doc, headers, rows, caption: str):
    add_caption(doc, caption)
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        set_run_font(run, bold=True, size=9)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(val))
            set_run_font(run, size=9)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def build():
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    # Title page block
    add_para(doc, "Zadanie 1 – Záverečný report", bold=True, size=16,
             align="center", first_line=False, space_after=6)
    add_para(doc, "Rozvrhovanie zákazníckych objednávok v permutačnej prietokovej výrobe",
             bold=True, size=14, align="center", first_line=False, space_after=6)
    add_para(doc,
             "Porovnanie simulovaného žíhania s iterovaným pažravým algoritmom "
             "(Hoffmann, Neufeld, Buscher, 2025)",
             italic=True, size=11, align="center", first_line=False, space_after=12)
    add_para(doc, "Predmet: Metaheuristiky a prírodou inšpirované optimalizačné algoritmy (MPO)",
             size=10, align="center", first_line=False, space_after=2)
    add_para(doc, "Variant B – návrh vlastného riešenia",
             size=10, align="center", first_line=False, space_after=2)
    add_para(doc, "[Doplňte mená členov tímu]",
             italic=True, size=10, align="center", first_line=False, space_after=18)

    # 1 Abstract
    add_heading(doc, "1 Abstrakt", 1)
    add_para(
        doc,
        "Práca sa zaoberá rozvrhovaním zákazníckych objednávok (Customer Order Scheduling "
        "Problem, COSP) v permutačnej prietokovej výrobe podľa článku Hoffmanna, Neufelda "
        "a Buschera [1]. Každá z n objednávok obsahuje o výrobných úloh spracovávaných "
        "na m strojoch; objednávka je dokončená až po spracovaní jej poslednej úlohy "
        "a cieľom je minimalizovať súčet časov dokončenia objednávok. Ako vlastné riešenie "
        "navrhujeme a implementujeme simulované žíhanie (SA) nad rovnakou permutačnou "
        "reprezentáciou, akú používa IGA-String. Baseline sme reimplementovali podľa "
        "pseudokódu autorov a porovnali so SA na rovnakých inštanciách a rovnakom "
        "výpočtovom rozpočte. Parametre SA sme nastavili na ladiach inštanciách; hlavné "
        "experimenty používajú rozpočet 190 000 vyhodnotení úplného rozvrhu na beh. "
        "Na malom teste (540 inštancií, 5,400 behov) dosiahlo SA priemerné RPD 0,008 % "
        "oproti 0,044 % pre IGA-String (jednostranný Wilcoxonov test, p ≈ 1,6·10⁻⁸). "
        "Na veľkom teste (135 inštancií, 1,350 behov) bolo RPD 0,389 % oproti 0,907 % "
        "(p ≈ 3,3·10⁻¹⁶). Doplnkové experimenty ukazujú, že na inštanciách s 500 úlohami "
        "je poradie pri 190 000 vyhodnoteniach citlivé na rozpočet a že výhoda SA "
        "nezávisí od štartu MultipleNEH."
    )

    # 2 Problem
    add_heading(doc, "2 Opis a význam riešeného problému", 1)
    add_para(
        doc,
        "Výrobca často odosiela zákazníkovi všetky výrobky jednej objednávky naraz. "
        "Objednávku preto možno expedovať až vtedy, keď sú hotové všetky jej položky; "
        "skoré dokončenie jednej položky nepomôže, ak sa iná dokončí neskoro. Túto "
        "závislosť zachytáva úloha COSP, ktorá hodnotí dokončenie celých objednávok, "
        "nie jednotlivých úloh [1, 3]."
    )
    add_para(
        doc,
        "Článok [1] skúma COSP v permutačnej prietokovej výrobe s m strojmi: každá úloha "
        "prechádza strojmi v rovnakom poradí a poradie úloh je na všetkých strojoch "
        "zhodné. V trojpoľovej notácii ide o úlohu Fm → 0 | prmu | ΣCi. Úloha je NP-ťažká "
        "už pre dva stroje [1, tvrdenie 1], čo vyplýva z NP-ťažkosti F2 || ΣCj [4] "
        "a odôvodňuje použitie heuristík."
    )
    add_para(
        doc,
        "Kritérium sa líši od celkového času výroby (makespan): rozvrh s krátkym "
        "makespanom nemusí byť výhodný, ak väčšina zákazníkov čaká takmer do konca "
        "výroby. Model neuvažuje termíny dodania ani priority, takže výsledok nemožno "
        "interpretovať ako minimalizáciu omeškania. Z hľadiska typu ide o minimalizačnú, "
        "diskrétnu, jednokriteriálnu úlohu s obmedzeniami. Je statická a deterministická "
        "a má charakter bielej skrinky (white-box)."
    )

    # 3 Formulation
    add_heading(doc, "3 Formulácia optimalizačnej úlohy", 1)
    add_heading(doc, "3.1 Rozhodovacie premenné a model autorov", 2)
    add_para(
        doc,
        "Vstup tvorí n objednávok po o úlohách, m strojov a časy spracovania p_{i j k} "
        "úlohy j objednávky i na stroji k; celkový počet úloh je N = n·o. Autori úlohu "
        "formulujú ako zmiešaný celočíselný nelineárny program (MINLP) s binárnou "
        "premennou x_{i j π}, ktorá má hodnotu 1 práve vtedy, keď je úloha (i, j) na "
        "pozícii π spoločnej postupnosti, a so spojitými premennými pre časy dokončenia "
        "úloh a objednávok [1, časti 3.1–3.2]. Podmienky zaručujú, že každá úloha obsadí "
        "práve jednu pozíciu a každá pozícia práve jednu úlohu; nelinearita vyplýva zo "
        "súčinov rozhodovacích a časových premenných."
    )
    add_heading(doc, "3.2 Permutačná reprezentácia a účelová funkcia", 2)
    add_para(
        doc,
        "Priradenie x je ekvivalentné permutácii Π všetkých N dvojíc (i, j); priestor "
        "kandidátov má N! prvkov. Túto reprezentáciu používa IGA-String aj naše SA, "
        "preto medzi metódami nie je potrebná transformácia riešení. Nech π_r je úloha "
        "na pozícii r a C(π_r, k) jej čas dokončenia na stroji k. Pre r = 1,…,N a "
        "k = 1,…,m platí"
    )
    add_para(
        doc,
        "C(π_r, 1) = C(π_{r−1}, 1) + p(π_r, 1),    "
        "C(π_r, k) = max{ C(π_{r−1}, k), C(π_r, k−1) } + p(π_r, k)  (k ≥ 2),",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "s C(π_0, ·) = 0. Objednávka i je dokončená, keď sa na poslednom stroji dokončí "
        "jej posledná úloha: Ci = max{ C(π_r, m) | π_r patrí do objednávky i }. "
        "Účelová funkcia je F(Π) = Σ_i Ci. Vyhodnotenie kandidáta vyžaduje O(N·m) "
        "operácií. Podľa lemy 2 článku vždy existuje optimálny rozvrh bez zámerne "
        "vložených prestojov [1]. Každá permutácia je prípustná, preto nie sú potrebné "
        "opravné ani penalizačné mechanizmy."
    )
    add_heading(doc, "3.3 Kontrolný príklad", 2)
    add_para(
        doc,
        "Protipríklad z článku [1, tab. 4] má n = 2, o = 2, m = 2. Pre rozvrh "
        "(2,2), (1,2), (1,1), (2,1) dáva rekurencia na druhom stroji časy 18, 20, 31 a 48, "
        "teda C₁ = 31, C₂ = 48 a F = 79, čo je optimum. Najlepší rozvrh so súvislými "
        "blokmi objednávok má hodnotu 80 [1, tab. 5]; súvislé bloky teda nemožno "
        "vyžadovať (lema 3). Tieto hodnoty sme overili vlastným výpočtom a používame "
        "ich ako jednotkové testy implementácie."
    )

    # 4 Authors' method
    add_heading(doc, "4 Opis metódy autorov článku", 1)
    add_para(
        doc,
        "Autori riešia MINLP solverom Gurobi (referencia pre malé inštancie) a navrhujú "
        "štyri heuristiky založené na iterovanom pažravom algoritme (IGA) [1, 5], "
        "ktoré hľadajú kvalitné riešenia v obmedzenom čase bez záruky optimality. "
        "Všetky varianty začínajú procedúrou MultipleNEH [1, alg. 1]: najprv NEH "
        "na úlohách každej objednávky (zoradenie vzostupne podľa celkového času "
        "spracovania – na rozdiel od klasickej NEH, ktorá triedi zostupne – a "
        "vkladanie podľa makespanu objednávky), potom NEH na celých objednávkach "
        "(vkladanie podľa F). Makespan je tu iba pomocným kritériom."
    )
    add_para(
        doc,
        "IGA-String upravuje jednu permutáciu všetkých N úloh. V každej iterácii sa "
        "odstráni d náhodných úloh, zoradia sa vzostupne podľa celkového času "
        "spracovania a každá sa vloží na pozíciu s najnižším F; lokálne prehľadávanie "
        "MultipleInsertion následne ⌊z·d/d_min⌋-krát presunie náhodnú úlohu na jej "
        "najlepšiu pozíciu. Lepší rozvrh sa prijme vždy; horší s pravdepodobnosťou"
    )
    add_para(
        doc,
        "q ≤ exp( −y · (d_min / d) · (F(Π′) − F(Π)) / F(Π) ),",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "kde q ∼ U[0,1]. Po zlepšení sa d nastaví na d_min, inak sa zväčší najviac "
        "po ⌊N/2⌋. Pravidlo pripomína Metropolisovo kritérium SA [7], úlohu teploty "
        "však zohráva adaptívne d, nie klesajúci plán chladenia. Nevýhodou je cena "
        "iterácie: každé skúšané vloženie vyžaduje prepočet celej permutácie."
    )
    add_para(
        doc,
        "Maticové varianty znižujú cenu iterácie úpravou kratších postupností "
        "(poradie úloh v objednávke a poradie objednávok). IGA-Matrix1 zachováva "
        "blokový rozvrh; Matrix2 a Matrix3 pridávajú LocalSearch3, ktorý výmenami "
        "s predchádzajúcou úlohou umožňuje prelínanie objednávok – podľa lemy 3 "
        "niekedy nevyhnutné. Matrix3 navyše hodnotí poradie úloh podľa F celého "
        "rozvrhu, nie podľa makespanu samotnej objednávky. Pre IGA-String autori "
        "volia y = 20 000 a z = 2 [1, tab. 8]. Experimentálny protokol autorov "
        "(časový limit n·o·m/2·0,12 s, 5 behov, RPD, Wilcoxonov test) je východiskom "
        "nášho porovnania; odchýlky uvádzame v časti 6."
    )

    # 5 Our method
    add_heading(doc, "5 Opis vlastného riešenia", 1)
    add_para(
        doc,
        "Vlastným riešením je simulované žíhanie na rovnakej permutácii všetkých úloh. "
        "Počiatočné riešenie je MultipleNEH (rovnako ako pri IGA), prípadne náhodná "
        "permutácia v ablácii. V každom kroku sa vykoná jedna náhodná zmena: s "
        "pravdepodobnosťou 0,6 presun úlohy, s 0,3 výmena dvoch úloh a s 0,1 presun "
        "celého bloku úloh jednej objednávky. Zlepšenie sa prijme vždy; zhoršenie Δ "
        "s pravdepodobnosťou exp(−Δ / T)."
    )
    add_para(
        doc,
        "Počiatočná teplota T₀ sa kalibruje na inštancii: zo vzorky 200 náhodných "
        "krokov sa vezme priemerné zhoršenie Δ⁺ a T₀ sa zvolí tak, aby sa priemerné "
        "zhoršenie prijalo s pravdepodobnosťou p₀, teda T₀ = −Δ⁺ / ln p₀. Teplota "
        "klesá geometricky s podielom spotrebovaného rozpočtu τ ∈ [0,1]:"
    )
    add_para(
        doc,
        "T(τ) = T₀ · r^τ,",
        align="center", first_line=False, italic=True, space_before=4, space_after=4,
    )
    add_para(
        doc,
        "kde r = t_ratio je pomer konečnej a počiatočnej teploty. Väzba na podiel "
        "rozpočtu zaručuje, že plán chladenia sa vždy ukončí na konci behu bez ohľadu "
        "na veľkosť inštancie. Implementácia je v Pythone 3.12; každý výsledok behu "
        "sa overuje nezávislou funkciou, ktorá počíta F z definičných časov začiatkov "
        "a koncov."
    )

    # 6 Differences
    add_heading(doc, "6 Prehľad rozdielov oproti pôvodnému článku", 1)
    add_para(
        doc,
        "Hlavný rozdiel je voľba metaheuristiky: namiesto IGA používame SA s "
        "geometrickým chladením a lacnými lokálnymi pohybmi. Baseline IGA-String sme "
        "reimplementovali podľa pseudokódu [1, alg. 2–6]; oproti článku kontrolujeme "
        "rozpočet aj medzi jednotlivými vkladaniami úloh (jedna iterácia IGA môže na "
        "veľkých inštanciách spotrebovať podstatnú časť limitu). IGA-Matrix1–3 a model "
        "MINLP sme neimplementovali; ich publikované RPD uvádzame ako sekundárnu "
        "referenciu."
    )
    add_para(
        doc,
        "Namiesto časového limitu n·o·m/2·t sekúnd (t = 0,12) používame pevný počet "
        "190 000 vyhodnotení úplného rozvrhu na beh. Dôvodom je reprodukovateľnosť: "
        "časový limit závisí od hardvéru a záťaže (počas ladenia parametrov laptop "
        "ušiel do spánku a niektoré behy dostali výrazne menej práce). Na vývojovom "
        "notebooku (Intel Core i7-9750H) zodpovedá 190 000 vyhodnotení približne "
        "množstvu práce, ktoré papierový časový limit kupoval pri súbehu štyroch "
        "behov. Veľký test sme navyše skrátili na 5 z 20 porovnávacích inštancií "
        "na veľkosť (čísla 10–14) z dôvodu výpočtového rozpočtu."
    )

    # 7 Methodology
    add_heading(doc, "7 Experimentálna metodológia", 1)
    add_para(
        doc,
        "Používame oficiálne inštancie autorov [2] (commit c3d1a47). Spracovacie časy "
        "sú z U[1, 100]. Správnosť účelovej funkcie sme overili na všetkých 90 "
        "inštanciách s n = 3, o = 2: optimum získané úplným prehľadaním sa zhoduje "
        "s najlepšou známou hodnotou v súboroch. Softvér: Python 3.12.10, Windows 10; "
        "behy bežali so 4 workerami."
    )
    add_table(
        doc,
        ["Položka", "Nastavenie"],
        [
            ["Ladenie SA", "9 kombinácií p₀ ∈ {0,01; 0,1; 0,3}, r ∈ {0,001; 0,01; 0,1}; "
             "3 veľkosti × 5 inštancií (č. 0–4) × 3 seed-y; papierový časový limit"],
            ["Malý test", "n ∈ {3,4,5}, o ∈ {2,3,4}, m ∈ {2,3,6}; inštancie 10–29; "
             "5 seed-ov; 190 000 vyhodnotení; SA a IGA-String"],
            ["Veľký test", "n ∈ {10,20,50}, o ∈ {2,5,10}, m ∈ {2,3,6}; inštancie 10–14; "
             "5 seed-ov; 190 000 vyhodnotení; SA a IGA-String"],
            ["Ablácia štartu", "5 veľkostí, inštancie 10–14, 5 seed-ov; SA-NEH vs SA-random"],
            ["Predĺžený rozpočet", "n = 50, o = 10, m ∈ {2,3,6}; 760 000 vyhodnotení"],
            ["Metrika", "RPD = 100·(F − F_ref)/F_ref [%]; F_ref = min(publikovaná hodnota, "
             "najlepší beh experimentu)"],
            ["Štatistika", "jednostranný Wilcoxonov znamienkový test na priemerných RPD "
             "inštancií, α = 0,05"],
            ["Parametre SA", "p₀ = 0,3, r = 0,001 (výber podľa najnižšieho priemerného RPD "
             "pri ladení); IGA-String: y = 20 000, z = 2"],
        ],
        "Tabuľka 1: Prehľad experimentálneho protokolu.",
    )
    add_para(
        doc,
        "Pri ladení dosiahla kombinácia p₀ = 0,3, r = 0,001 najnižšie priemerné RPD "
        "(0,234 %), bez signifikantného rozdielu oproti trom ďalším nastaveniam "
        "s RPD 0,27–0,31 %. Všetky nastavenia s r = 0,1 boli signifikantne horšie. "
        "Vybrané hodnoty sú zároveň predvolenými hodnotami implementácie."
    )

    # 8 Results
    add_heading(doc, "8 Dosiahnuté výsledky", 1)
    add_heading(doc, "8.1 Malý test", 2)
    add_para(
        doc,
        "Na 540 inštanciách (5,400 behov) dosiahlo SA priemerné RPD 0,008 % a IGA-String "
        "0,044 %. Medián oboch metód je 0. SA dosiahlo referenčnú hodnotu v 97,6 % "
        "behov a IGA-String v 92,0 %. Jednostranný Wilcoxonov test na 540 inštanciách "
        "potvrdzuje prevahu SA (p ≈ 1,6·10⁻⁸). Na 469 inštanciách majú obe metódy "
        "rovnaké priemerné RPD; rozdiel vzniká najmä pri väčších veľkostiach "
        "(n = 5, o ∈ {3,4}). Na 19 inštanciách sme zlepšili publikovanú najlepšiu "
        "známu hodnotu (priemerné zlepšenie 0,24 %); žiadna z nich nepatrí medzi "
        "inštancie, pre ktoré autori uvádzajú dokázané optimum."
    )
    add_table(
        doc,
        ["Metóda", "Priem. RPD [%]", "Medián", "σ", "Zásah referencie [%]", "Priem. čas [s]"],
        [
            ["SA", "0,008", "0,000", "0,073", "97,6", "2,99"],
            ["IGA-String", "0,044", "0,000", "0,216", "92,0", "2,45"],
        ],
        "Tabuľka 2: Súhrn výsledkov na malom teste (540 inštancií, 5 seed-ov).",
    )
    add_figure(
        doc, FIG / "small_convergence.png",
        caption="Obrázok 1: Konvergencia na malom teste – priemerné RPD najlepšieho "
        "riešenia vzhľadom na podiel spotrebovaného rozpočtu.",
    )
    add_para(
        doc,
        "IGA-String vedie približne v prvej tretine rozpočtu; SA ho prekoná okolo "
        "35 % a potom zostáva blízko nuly. Pri výrazne menšom rozpočte by sa poradie "
        "pravdepodobne otočilo."
    )

    add_heading(doc, "8.2 Veľký test", 2)
    add_para(
        doc,
        "Na 135 inštanciách (1,350 behov) je priemerné RPD SA 0,389 % a IGA-String "
        "0,907 % (p ≈ 3,3·10⁻¹⁶). SA je lepšie na 109 inštanciách, IGA-String na 25. "
        "Priemerný čas behu je takmer rovnaký (26,0 s vs. 25,0 s), takže nerovnosť "
        "v čase na vyhodnotenie je tu malá. Na 70 inštanciách sme našli lepšiu hodnotu, "
        "než je v súboroch autorov (65 výhradne SA)."
    )
    add_table(
        doc,
        ["Metóda", "Priem. RPD [%]", "Medián", "σ", "Zásah referencie [%]", "Priem. čas [s]"],
        [
            ["SA", "0,389", "0,339", "0,345", "18,4", "26,0"],
            ["IGA-String", "0,907", "0,823", "0,624", "6,8", "25,0"],
        ],
        "Tabuľka 3: Súhrn výsledkov na veľkom teste (135 inštancií, 5 seed-ov).",
    )
    add_figure(
        doc, FIG / "big_convergence.png",
        caption="Obrázok 2: Konvergencia na veľkom teste. SA prekoná IGA-String "
        "približne pri 63 % rozpočtu; na konci ešte klesá.",
    )
    add_figure(
        doc, FIG / "big_rpd_by_factor.png", width_cm=12.5,
        caption="Obrázok 3: Priemerné RPD s 95 % intervalom spoľahlivosti podľa n, o "
        "a m (veľký test).",
    )
    add_para(
        doc,
        "Výnimkou sú inštancie s 500 úlohami (n = 50, o = 10): pri 190 000 "
        "vyhodnoteniach je IGA-String lepšie na 11 z 15 inštancií (RPD 0,600 % "
        "oproti 0,735 %). SA tu vykoná iba približne 380 krokov na úlohu, čo "
        "naznačuje nedokonvergovanie; túto hypotézu overujeme v časti 8.4."
    )

    add_heading(doc, "8.3 Ablácia počiatočného riešenia", 2)
    add_para(
        doc,
        "Na piatich veľkostiach (25 inštancií) sme porovnali SA štartujúce z "
        "MultipleNEH a z náhodnej permutácie pri rovnakom rozpočte 190 000 "
        "vyhodnotení. Náhodný štart má priemernú medzeru voči najlepšej známej "
        "hodnote na začiatku 81 %, NEH iba 2 %; napriek tomu náhodný štart končí "
        "lepšie (priemerné RPD 0,369 % oproti 0,429 %, Wilcoxon na absolútnych "
        "hodnotách F, p = 0,041). Výhoda SA teda nevyplýva z MultipleNEH; pri "
        "zvolenom pláne chladenia môže dobrý štart dokonca obmedziť prieskum."
    )

    add_heading(doc, "8.4 Predĺžený rozpočet na 500 úlohách", 2)
    add_para(
        doc,
        "Rovnakých 15 inštancií s 500 úlohami sme prepočítali so štvornásobným "
        "rozpočtom (760 000 vyhodnotení). Voči spoločnej referencii (minimum z "
        "oboch experimentov a publikovanej hodnoty) kleslo RPD SA z 0,779 % na "
        "0,263 % a IGA-String z 0,643 % na 0,513 %. Pri 760 000 vyhodnoteniach "
        "SA vyhráva na 11 z 15 inštancií (Wilcoxon p = 0,011); pri 190 000 "
        "prehrávalo (p = 0,93 pre hypotézu, že SA je lepšie). Posledné zlepšenie "
        "SA typicky prichádza až pri 99,8 % rozpočtu. Prehra SA na 500 úlohách "
        "v hlavnom experimente je teda dôsledok nedostatočného rozpočtu, nie "
        "systematickej slabiny metódy."
    )
    add_table(
        doc,
        ["m", "SA @190k", "IGA @190k", "SA @760k", "IGA @760k"],
        [
            ["2", "0,598", "0,772", "0,298", "0,757"],
            ["3", "0,621", "0,570", "0,353", "0,527"],
            ["6", "1,116", "0,587", "0,139", "0,255"],
            ["spolu", "0,779", "0,643", "0,263", "0,513"],
        ],
        "Tabuľka 4: Priemerné RPD [%] na 15 inštanciách s 500 úlohami pri dvoch "
        "rozpočtoch (spoločná referencia).",
    )
    # 9 Comparison with authors
    add_heading(doc, "9 Porovnanie s výsledkami autorov", 1)
    add_para(
        doc,
        "Tabuľka 5 uvádza naše RPD vedľa hodnôt z [1]. Porovnanie nie je priamou "
        "replikáciou: iný hardvér, pevný počet vyhodnotení namiesto času, na veľkom "
        "teste 5 z 20 inštancií a striknejšia referencia F_ref (19 + 70 nových "
        "najlepších hodnôt). Naša IGA-String je blízko publikovanej hodnoty na malom "
        "teste; na veľkom teste je vyššia, čo je konzistentné so striknejšou "
        "referenciou. SA na veľkom teste leží v pásme publikovaných IGA-Matrix "
        "variantov, no bez ich behu za rovnakých podmienok to nie je dôkaz prevahy."
    )
    add_table(
        doc,
        ["Test / metóda", "Naše RPD [%]", "Publikované RPD [%]"],
        [
            ["Small / IGA-String", "0,044", "0,058"],
            ["Small / SA", "0,008", "—"],
            ["Big / IGA-String", "0,907", "0,817"],
            ["Big / SA", "0,389", "—"],
            ["Big / IGA-Matrix1–3 (iba [1])", "—", "0,32–0,44"],
        ],
        "Tabuľka 5: Orientačné porovnanie s publikovanými výsledkami [1].",
    )

    # 10 Discussion
    add_heading(doc, "10 Diskusia", 1)
    add_para(
        doc,
        "SA ťaží z veľkého počtu lacných krokov (rádovo 10⁵ na beh) oproti stovkám "
        "až tisícom drahých iterácií IGA-String, čo vysvetľuje neskorší, ale "
        "strmší pokles RPD. IGA-String je lepší pri krátkom rozpočte; SA pri "
        "vyčerpaní celého limitu. Rovnaký počet vyhodnotení nie je rovnaký čas: "
        "na malom teste trval beh SA o 22 % dlhšie (2,99 s oproti 2,45 s), na "
        "veľkom teste iba o 4 %. Časť výhody SA na malom teste teda môže súvisieť "
        "s mierne väčším časom; IGA-String je však na konci rozpočtu už takmer "
        "plochý. Ablácia ukazuje, že MultipleNEH nie je nutnou podmienkou kvality "
        "SA. Pevný počet vyhodnotení navyše nedáva všetkým veľkostiam rovnakú "
        "hĺbku prieskumu (počet krokov na úlohu klesá s N), čo papierový časový "
        "limit rastúci s n·o·m čiastočne rieši."
    )

    # 11 Limitations
    add_heading(doc, "11 Obmedzenia", 1)
    add_para(
        doc,
        "Neimplementovali sme IGA-Matrix1–3 ani MINLP/Gurobi. Veľký test pokrýva "
        "iba 5 z 20 inštancií na veľkosť. Rozpočet v počte vyhodnotení sa líši od "
        "protokolu autorov a na malom teste mierne zvýhodňuje SA v čase. Ladenie "
        "prebehlo na troch veľkostiach; víťazné nastavenie leží v rohu mriežky "
        "a nie je signifikantne lepšie než niekoľko susedov. Výsledky sú viazané "
        "na jednu implementáciu v čistom Pythone na jednom notebooku."
    )

    # 12 Conclusion
    add_heading(doc, "12 Záver", 1)
    add_para(
        doc,
        "Navrhli a implementovali sme simulované žíhanie pre COSP v permutačnej "
        "prietokovej výrobe a férovo sme ho porovnali s reimplementáciou IGA-String "
        "z článku [1]. Pri rozpočte 190 000 vyhodnotení na beh SA signifikantne "
        "prekonáva IGA-String na malom aj veľkom teste. Poradie však závisí od "
        "rozpočtu a veľkosti: IGA-String je lepší skoro v behu a na 500 úlohách "
        "pri hlavnom rozpočte; so štvornásobným rozpočtom SA na týchto inštanciách "
        "opäť vedie. Ablácia ukázala, že výhoda SA nezávisí od štartu MultipleNEH. "
        "Pre ďalšiu prácu považujeme za užitočné porovnať SA s IGA-Matrix3 za "
        "rovnakých podmienok a viazať rozpočet na počet úloh, nie iba na pevný "
        "počet vyhodnotení."
    )

    # 13 Literature
    add_heading(doc, "13 Zoznam použitej literatúry", 1)
    refs = [
        "[1] HOFFMANN, J., NEUFELD, J. S., BUSCHER, U. Customer order scheduling in a "
        "permutation flow shop environment. Operations Research Perspectives, 2025, 15, "
        "100362. https://doi.org/10.1016/j.orp.2025.100362",
        "[2] HOFFMANN, J. COSP_Flow_Shop: problémové inštancie [online]. GitHub "
        "[cit. 2026-11-14]. Dostupné na: https://github.com/Julius2627/COSP_Flow_Shop",
        "[3] FRAMINAN, J. M., PEREZ-GONZALEZ, P., FERNANDEZ-VIAGAS, V. Deterministic "
        "assembly scheduling problems: A review and classification of concurrent-type "
        "scheduling models and solution procedures. European Journal of Operational "
        "Research, 2019, 273(2), 401–417.",
        "[4] GAREY, M. R., JOHNSON, D. S., SETHI, R. The complexity of flowshop and "
        "jobshop scheduling. Mathematics of Operations Research, 1976, 1(2), 117–129.",
        "[5] HOFFMANN, J., NEUFELD, J. S., BUSCHER, U. Iterated greedy algorithms for "
        "customer order scheduling with dedicated machines. IFAC-PapersOnLine, 2022, "
        "55(10), 1594–1599.",
        "[6] NAWAZ, M., ENSCORE, E. E., HAM, I. A heuristic algorithm for the m-machine, "
        "n-job flow-shop sequencing problem. Omega, 1983, 11(1), 91–95.",
        "[7] KIRKPATRICK, S., GELATT, C. D., VECCHI, M. P. Optimization by simulated "
        "annealing. Science, 1983, 220(4598), 671–680.",
    ]
    for ref in refs:
        p = add_para(doc, ref, size=10, align="left", first_line=False,
                     space_after=4, space_before=0)
        p.paragraph_format.left_indent = Cm(0.75)
        p.paragraph_format.first_line_indent = Cm(-0.75)

    add_heading(doc, "Príloha: Poznámka k použitiu nástrojov", 1)
    add_para(
        doc,
        "Zdrojový kód experimentov, konfigurácie a prvá verzia tohto reportu vznikli "
        "s pomocou AI asistenta (Cursor) v novembri 2026. Analýza problému, návrh "
        "experimentov, interpretácia výsledkov a finálne znenie reportu sú výsledkom "
        "vlastnej práce tímu. Inštancie [2] pochádzajú od autorov článku; IGA-String "
        "je reimplementácia podľa ich pseudokódu."
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
