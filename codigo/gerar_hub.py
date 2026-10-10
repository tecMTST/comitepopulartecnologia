#!/usr/bin/env python3
"""
Hub de Iniciativas Digitais — Gerador de HTML
==============================================
Este script:
1. Lê o CSV atualizado (tabela_categorias_normalizadas.csv)
2. Gera o HTML final com os dados embutidos inline
3. Abre o resultado no browser via servidor HTTP local

Execute sempre que o CSV for atualizado:
    python3 gerar_hub.py

Ou para só servir sem regenerar:
    python3 iniciar_hub.py
"""

import csv
import json
import os
import sys
import re
import http.server
import socketserver
import webbrowser
import threading
import time
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE   = os.path.join(DIR, 'tabela_categorias_normalizadas.csv')
HTML_OUT   = os.path.join(DIR, 'hub_de_iniciativas_digitais.html')
PORT       = 8080


# ─── Leitura do CSV ──────────────────────────────────────────────
def read_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get('Nome da Iniciativa') or '').strip()
            if not name:
                continue
            rows.append({
                'nome': name,
                'link': (row.get('Link') or '').strip(),
                'desc': (row.get('Breve Descrição') or '').strip(),
                'cat':  (row.get('Categoria 1') or '').strip(),
            })
    return rows


# ─── HTML Template ────────────────────────────────────────────────
def build_html(rows, generated_at):
    data_json = json.dumps(rows, ensure_ascii=False)
    total     = len(rows)
    cats      = sorted(set(r['cat'] for r in rows if r['cat']))

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hub de Iniciativas Digitais | Comitê Popular do Lula</title>
    <meta name="description" content="Explore, acesse e compartilhe as principais plataformas e ferramentas digitais para fortalecer a militância e o trabalho de base do Comitê Popular do Lula.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&display=swap" rel="stylesheet">
    <style>
        /* ── TOKENS ───────────────────────────────── */
        :root {{
            --red:    #C3090A; --red-d:  #A00708;
            --green:  #0B912A; --grn-d:  #087A23;
            --yellow: #FBCE02;
            --blue:   #048ED6; --blu-d:  #0270AA;
            --ink:    #2A2A2A; --ink-m:  #5E5E5E;
            --brd:    #D9D4CC; --brd-s:  #8A847B;
            --surf:   #FFFFFF; --surf-a: #F3F1EE;
            --info-bg:#E1F1FA; --info:   #015A8A;
            --max-w:  1200px;
            --r-sm: 4px; --r-md: 8px; --r-lg: 16px; --r-pill: 9999px;
            --sh1: 0 2px 6px rgba(0,0,0,.07);
            --sh2: 0 4px 18px rgba(0,0,0,.13);
        }}

        /* ── RESET ────────────────────────────────── */
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html {{ scroll-behavior: smooth; }}
        body {{
            font-family: 'Montserrat', system-ui, sans-serif;
            font-size: 1rem; font-weight: 500;
            color: var(--ink); background: var(--surf-a);
            min-height: 100vh; display: flex; flex-direction: column;
            -webkit-tap-highlight-color: transparent;
            line-height: 1.55;
        }}
        a {{ color: inherit; text-decoration: none; }}
        img {{ max-width: 100%; display: block; }}

        /* ── FOCUS ────────────────────────────────── */
        :focus-visible {{
            outline: none !important;
            box-shadow: 0 0 0 3px #fff, 0 0 0 6px var(--ink) !important;
            border-radius: var(--r-sm);
        }}
        .dark-bg :focus-visible {{
            box-shadow: 0 0 0 3px var(--yellow) !important;
        }}
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{ animation-duration: .01ms !important; transition-duration: .01ms !important; }}
        }}

        /* ── LAYOUT ───────────────────────────────── */
        .wrap {{ width: 100%; max-width: var(--max-w); margin-inline: auto; padding-inline: 1rem; }}
        @media (min-width: 768px)  {{ .wrap {{ padding-inline: 1.5rem; }} }}
        @media (min-width: 1024px) {{ .wrap {{ padding-inline: 2rem; }} }}

        /* ── HEADER ───────────────────────────────── */
        .site-hdr {{ background: var(--red); color: #fff; box-shadow: var(--sh2); position: relative; z-index: 10; }}
        .flag {{ display: flex; height: 6px; }}
        .flag span:nth-child(1) {{ flex: 1; background: var(--blu-d); }}
        .flag span:nth-child(2) {{ flex: 1; background: var(--yellow); }}
        .flag span:nth-child(3) {{ flex: 1; background: var(--grn-d); }}
        .flag span:nth-child(4) {{ flex: 1; background: var(--red); }}

        .hdr-inner {{ display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding-block: 1rem; flex-wrap: wrap; }}
        .brand {{ display: flex; align-items: center; gap: .75rem; }}
        .brand-bdg {{ background: #fff; border-radius: var(--r-md); padding: .5rem .75rem; line-height: 1.2; box-shadow: var(--sh1); flex-shrink: 0; }}
        .brand-bdg .b1 {{ font-size: 9px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--blu-d); }}
        .brand-bdg .b2 {{ font-size: 13px; font-weight: 900; color: var(--grn-d); }}
        .brand-bdg .b3 {{ font-size: 9px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--red); }}
        .brand-txt .lbl {{ display: block; font-size: .7rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: var(--yellow); margin-bottom: 2px; }}
        .brand-txt h1 {{ font-size: clamp(1.1rem, 4vw, 1.55rem); font-weight: 900; color: #fff; line-height: 1.1; }}
        .hdr-tag {{ display: none; background: var(--red-d); border: 1px solid rgba(255,255,255,.15); color: #fff; font-size: .7rem; font-weight: 800; text-transform: uppercase; letter-spacing: .07em; padding: .25rem .75rem; border-radius: var(--r-pill); }}
        @media (min-width: 640px) {{ .hdr-tag {{ display: inline-block; }} }}

        /* Stats bar */
        .stats-bar {{ background: rgba(0,0,0,.18); padding: .375rem 0; font-size: .75rem; font-weight: 700; color: rgba(255,255,255,.85); }}
        .stats-inner {{ display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; }}
        .stat {{ display: flex; align-items: center; gap: .4rem; }}
        .stat-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--yellow); animation: pulse-dot 2.5s ease-in-out infinite; flex-shrink: 0; }}
        @keyframes pulse-dot {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.5;transform:scale(.7)}} }}
        .stat em {{ color: var(--yellow); font-style: normal; font-weight: 900; }}

        /* ── HERO / SEARCH ────────────────────────── */
        .hero {{ background: var(--surf); border-bottom: 1px solid var(--brd); padding-block: 2rem; }}
        @media (min-width: 768px) {{ .hero {{ padding-block: 3rem; }} }}
        .hero-title {{ font-size: clamp(1.5rem, 1.1rem + 1.5vw, 2rem); font-weight: 900; color: var(--ink); line-height: 1.15; margin-bottom: .75rem; }}
        .hero-title em {{ font-style: normal; color: var(--red); }}
        .hero-desc {{ font-size: 1rem; color: var(--ink-m); max-width: 60ch; margin-bottom: 1.5rem; }}
        @media (min-width: 768px) {{ .hero-desc {{ font-size: 1.1rem; }} }}

        /* Search */
        .search-box {{ position: relative; max-width: 680px; }}
        .search-ico {{ position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--brd-s); pointer-events: none; }}
        #searchInput {{
            width: 100%; height: 52px; padding: 0 3rem 0 3rem;
            background: var(--surf); border: 1.5px solid var(--brd-s);
            border-radius: var(--r-pill); font-family: inherit;
            font-size: 1rem; font-weight: 500; color: var(--ink);
            transition: border-color .15s;
        }}
        #searchInput::placeholder {{ color: var(--ink-m); }}
        #searchInput:focus {{ outline: none; border-color: var(--ink); }}
        #clearBtn {{
            position: absolute; right: .75rem; top: 50%; transform: translateY(-50%);
            background: none; border: none; cursor: pointer; color: var(--ink-m);
            display: none; width: 32px; height: 32px; border-radius: 50%;
            align-items: center; justify-content: center;
        }}
        #clearBtn:hover {{ color: var(--ink); }}

        /* Pills */
        .pills-lbl {{ font-size: .7rem; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-m); margin-top: 1.5rem; margin-bottom: .75rem; }}
        .pills-row {{ display: flex; gap: .5rem; overflow-x: auto; padding-bottom: .5rem; scrollbar-width: none; -ms-overflow-style: none; }}
        .pills-row::-webkit-scrollbar {{ display: none; }}
        .pill {{
            display: inline-flex; align-items: center; gap: .3rem; white-space: nowrap;
            height: 44px; padding: 0 1rem; border-radius: var(--r-pill);
            border: 1.5px solid var(--brd); background: var(--surf);
            color: var(--ink); font-family: inherit; font-size: .75rem;
            font-weight: 800; cursor: pointer;
            transition: background .15s, border-color .15s, color .15s;
        }}
        .pill:hover {{ background: var(--surf-a); }}
        .pill.active {{ background: var(--red); border-color: var(--red); color: #fff; }}
        .pill-n {{ font-size: 10px; font-weight: 900; padding: 2px 6px; border-radius: 99px; background: var(--surf-a); color: var(--ink-m); }}
        .pill.active .pill-n {{ background: rgba(255,255,255,.2); color: #fff; }}

        /* ── MAIN ─────────────────────────────────── */
        main {{ flex: 1; padding-block: 2rem; }}
        @media (min-width: 768px) {{ main {{ padding-block: 3rem; }} }}

        /* Filter status */
        .flt-bar {{ display: none; align-items: center; justify-content: space-between; gap: .75rem; background: var(--info-bg); border: 1.5px solid var(--blu-d); border-radius: var(--r-md); padding: .75rem 1rem; margin-bottom: 1.5rem; font-size: .875rem; font-weight: 700; color: var(--info); }}
        .flt-bar.on {{ display: flex; }}
        .flt-bar button {{ background: none; border: none; cursor: pointer; font: inherit; font-weight: 800; color: var(--blu-d); text-decoration: underline; min-height: 44px; padding: 0 .5rem; white-space: nowrap; }}

        /* Loading */
        .loader {{ text-align: center; padding: 4rem 1rem; }}
        .spinner {{ width: 44px; height: 44px; border: 4px solid var(--brd); border-top-color: var(--red); border-radius: 50%; animation: spin .7s linear infinite; margin: 0 auto 1rem; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .loader p {{ color: var(--ink-m); font-weight: 700; }}

        /* Sections */
        #hub {{ display: flex; flex-direction: column; gap: 3rem; }}
        .cat-section {{}}
        .cat-hdr {{ display: flex; align-items: center; gap: .75rem; border-bottom: 2.5px solid var(--red); padding-bottom: .75rem; margin-bottom: 1rem; }}
        .cat-bar {{ width: 12px; height: 28px; border-radius: var(--r-sm); flex-shrink: 0; }}
        .cat-hdr h2 {{ font-size: clamp(1rem, .8rem + .8vw, 1.35rem); font-weight: 900; color: var(--ink); text-transform: uppercase; letter-spacing: .04em; flex: 1; }}
        .cat-cnt {{ font-size: .7rem; font-weight: 800; color: var(--ink-m); background: rgba(0,0,0,.06); padding: 4px 10px; border-radius: var(--r-pill); white-space: nowrap; }}

        /* Grid */
        .grid {{ display: grid; grid-template-columns: 1fr; gap: 1rem; }}
        @media (min-width: 560px)  {{ .grid {{ grid-template-columns: repeat(2,1fr); }} }}
        @media (min-width: 1024px) {{ .grid {{ grid-template-columns: repeat(3,1fr); gap: 1.5rem; }} }}

        /* Card */
        .card {{ background: var(--surf); border: 1.5px solid var(--brd); border-radius: var(--r-md); padding: 1rem; box-shadow: var(--sh1); display: flex; flex-direction: column; transition: border-color .2s, box-shadow .2s, transform .15s; }}
        .card:hover {{ border-color: var(--brd-s); box-shadow: var(--sh2); transform: translateY(-2px); }}
        @media (min-width: 768px) {{ .card {{ padding: 1.25rem; }} }}
        .card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: .5rem; margin-bottom: .75rem; }}
        .cat-badge {{ display: inline-block; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: .07em; color: var(--blu-d); background: var(--surf-a); border: 1px solid var(--brd); padding: 3px 8px; border-radius: var(--r-sm); flex-shrink: 0; max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .card-domain {{ font-size: 10px; font-weight: 700; color: var(--brd-s); font-family: 'Courier New', monospace; max-width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; text-align: right; }}
        .card-title {{ font-size: 1rem; font-weight: 800; color: var(--ink); line-height: 1.3; margin-bottom: auto; padding-bottom: 1rem; }}
        @media (min-width: 768px) {{ .card-title {{ font-size: 1.05rem; }} }}

        /* Accordion */
        .acc-wrap {{ border-top: 1px solid var(--brd); padding-top: .75rem; margin-bottom: .75rem; }}
        .acc-btn {{ display: flex; align-items: center; justify-content: space-between; width: 100%; background: none; border: none; cursor: pointer; font-family: inherit; font-size: .8rem; font-weight: 800; color: var(--blu-d); text-align: left; min-height: 44px; padding-block: .25rem; transition: color .15s; }}
        .acc-btn:hover {{ color: var(--blue); }}
        .acc-btn span {{ text-decoration: underline; text-underline-offset: 3px; }}
        .chevron {{ width: 16px; height: 16px; transition: transform .25s ease; flex-shrink: 0; color: currentColor; }}
        .acc-btn[aria-expanded="true"] .chevron {{ transform: rotate(180deg); }}
        .acc-body {{ display: grid; grid-template-rows: 0fr; transition: grid-template-rows .25s ease-out, opacity .2s ease-out; opacity: 0; }}
        .acc-body.open {{ grid-template-rows: 1fr; opacity: 1; }}
        .acc-inner {{ overflow: hidden; }}
        .acc-desc {{ font-size: .8rem; color: var(--ink-m); line-height: 1.6; background: var(--surf-a); border: 1px solid var(--brd); border-radius: var(--r-md); padding: .75rem; margin-top: .5rem; font-weight: 500; }}

        /* Buttons */
        .actions {{ display: flex; gap: .5rem; align-items: center; }}
        .btn-p {{ flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 5px; height: 44px; padding: 0 1rem; background: var(--red); color: #fff; border: none; border-radius: var(--r-pill); font-family: inherit; font-size: .8rem; font-weight: 800; cursor: pointer; text-decoration: none; transition: background .15s; white-space: nowrap; }}
        .btn-p:hover {{ background: var(--red-d); }}
        .btn-p svg {{ width: 14px; height: 14px; flex-shrink: 0; }}
        .btn-o {{ display: inline-flex; align-items: center; justify-content: center; gap: 4px; height: 44px; min-width: 44px; padding: 0 .75rem; background: var(--surf); color: var(--ink); border: 1.5px solid var(--brd-s); border-radius: var(--r-pill); font-family: inherit; font-size: .8rem; font-weight: 800; cursor: pointer; transition: background .15s, border-color .15s; white-space: nowrap; }}
        .btn-o:hover {{ background: var(--surf-a); }}
        .btn-o svg {{ width: 14px; height: 14px; flex-shrink: 0; }}
        .btn-o .lbl {{ display: none; }}
        @media (min-width: 400px) {{ .btn-o .lbl {{ display: inline; }} }}

        /* Empty state */
        .empty {{ display: none; text-align: center; padding: 4rem 1rem; background: var(--surf); border: 1.5px solid var(--brd); border-radius: var(--r-lg); box-shadow: var(--sh1); }}
        .empty.on {{ display: block; }}
        .empty-ico {{ width: 60px; height: 60px; background: var(--surf-a); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; color: var(--red-d); }}
        .empty h3 {{ font-size: 1.2rem; font-weight: 800; margin-bottom: .5rem; }}
        .empty p {{ color: var(--ink-m); max-width: 36ch; margin: 0 auto 1.5rem; }}

        /* Toast */
        #toast {{ position: fixed; bottom: 1.5rem; left: 50%; transform: translateX(-50%) translateY(calc(100% + 1.5rem)); background: var(--ink); color: #fff; font-size: .85rem; font-weight: 800; padding: .75rem 1.5rem; border-radius: var(--r-pill); border: 2px solid var(--yellow); box-shadow: var(--sh2); display: flex; align-items: center; gap: .5rem; z-index: 1000; pointer-events: none; opacity: 0; transition: transform .3s cubic-bezier(.34,1.56,.64,1), opacity .25s; white-space: nowrap; max-width: calc(100vw - 2rem); }}
        #toast.on {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
        #toast svg {{ color: var(--yellow); width: 16px; height: 16px; flex-shrink: 0; }}

        /* Scroll top */
        #scrollTop {{ position: fixed; right: 1rem; bottom: 1.5rem; width: 46px; height: 46px; border-radius: 50%; background: var(--red); color: #fff; border: none; cursor: pointer; box-shadow: var(--sh2); display: flex; align-items: center; justify-content: center; z-index: 100; opacity: 0; pointer-events: none; transition: opacity .25s, transform .2s; transform: scale(.8); }}
        #scrollTop.on {{ opacity: 1; pointer-events: auto; transform: scale(1); }}
        #scrollTop:hover {{ background: var(--red-d); }}
        #scrollTop svg {{ width: 20px; height: 20px; }}

        /* Footer */
        .site-ftr {{ background: var(--ink); color: #fff; border-top: 4px solid var(--red); padding-block: 2rem; margin-top: auto; }}
        .ftr-inner {{ display: flex; flex-direction: column; gap: 1.5rem; }}
        @media (min-width: 768px) {{ .ftr-inner {{ flex-direction: row; align-items: center; justify-content: space-between; }} }}
        .ftr-brand {{ font-size: 1rem; font-weight: 900; color: var(--yellow); text-transform: uppercase; letter-spacing: .04em; margin-bottom: .25rem; }}
        .ftr-desc {{ font-size: .8rem; color: var(--brd); max-width: 42ch; }}
        .ftr-live {{ display: inline-flex; align-items: center; gap: .35rem; font-size: .7rem; font-weight: 700; color: #0B912A; margin-top: .5rem; }}
        .ftr-live .dot {{ width: 6px; height: 6px; border-radius: 50%; background: #0B912A; animation: pulse-dot 2s ease-in-out infinite; }}
        .ftr-meta {{ font-size: .7rem; color: var(--brd-s); text-align: left; }}
        @media (min-width: 768px) {{ .ftr-meta {{ text-align: right; }} }}
        .ftr-meta p+p {{ margin-top: .25rem; }}
    </style>
</head>
<body>

<!-- HEADER -->
<header class="site-hdr dark-bg" role="banner">
    <div class="flag" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
    <div class="wrap">
        <div class="hdr-inner">
            <div class="brand">
                <div class="brand-bdg" aria-label="Comitê Popular do Lula">
                    <div class="b1">Comitê</div>
                    <div class="b2">Popular</div>
                    <div class="b3">do Lula</div>
                </div>
                <div class="brand-txt">
                    <span class="lbl">Militância Digital</span>
                    <h1>Hub de Iniciativas Digitais</h1>
                </div>
            </div>
            <span class="hdr-tag">Ferramentas Oficiais &amp; Comunitárias</span>
        </div>
    </div>
    <div class="stats-bar">
        <div class="wrap">
            <div class="stats-inner">
                <div class="stat"><span class="stat-dot"></span><span><em id="sTotal">{total}</em> iniciativas</span></div>
                <div class="stat"><span class="stat-dot"></span><span><em id="sCats">{len(cats)}</em> categorias</span></div>
                <div class="stat"><span class="stat-dot"></span><span>Atualizado em <em>{generated_at}</em></span></div>
            </div>
        </div>
    </div>
</header>

<!-- HERO / SEARCH -->
<section class="hero" aria-labelledby="heroTitle">
    <div class="wrap">
        <h2 class="hero-title" id="heroTitle">
            Conecte-se às<br><em>ferramentas da militância</em>
        </h2>
        <p class="hero-desc">
            Explore, acesse e compartilhe as principais plataformas e ferramentas digitais para fortalecer a mobilização e o trabalho de base.
        </p>
        <div class="search-box">
            <svg class="search-ico" fill="none" stroke="currentColor" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input type="search" id="searchInput" placeholder="Buscar por nome, categoria ou palavra-chave…" aria-label="Buscar iniciativas" autocomplete="off">
            <button id="clearBtn" aria-label="Limpar busca" title="Limpar busca">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="16" height="16"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
        </div>
        <p class="pills-lbl">Filtrar por categoria:</p>
        <div class="pills-row" id="pillsRow" role="group" aria-label="Filtros de categoria"></div>
    </div>
</section>

<!-- MAIN -->
<main id="main">
    <div class="wrap">
        <div class="flt-bar" id="fltBar" role="status" aria-live="polite">
            <span id="fltTxt"></span>
            <button onclick="reset()">Mostrar todas</button>
        </div>
        <div id="hub" aria-label="Iniciativas por categoria"></div>
        <div class="empty" id="empty" role="status">
            <div class="empty-ico" aria-hidden="true">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="30" height="30">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <h3>Nenhuma iniciativa encontrada</h3>
            <p>Tente ajustar o termo de busca ou selecionar outra categoria.</p>
            <button class="btn-p" onclick="reset()" style="display:inline-flex;width:auto;min-width:180px;">Ver todas as iniciativas</button>
        </div>
    </div>
</main>

<!-- TOAST -->
<div id="toast" role="alert" aria-live="assertive">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>
    <span id="toastMsg">Link copiado!</span>
</div>

<!-- SCROLL TOP -->
<button id="scrollTop" aria-label="Voltar ao topo" title="Voltar ao topo">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 15l7-7 7 7"/></svg>
</button>

<!-- FOOTER -->
<footer class="site-ftr" role="contentinfo">
    <div class="wrap">
        <div class="ftr-inner">
            <div>
                <div class="ftr-brand">Comitê Popular do Lula</div>
                <p class="ftr-desc">Hub centralizado de ferramentas, apps e repositórios para organização, diálogo e mobilização popular digital.</p>
                <div class="ftr-live"><span class="dot"></span>Base gerada automaticamente via CSV</div>
            </div>
            <div class="ftr-meta">
                <p>Guia de Interface Web &amp; Apps · Outubro 2026</p>
                <p>Desenvolvido mobile-first com foco em acessibilidade</p>
                <p>Gerado em {generated_at}</p>
            </div>
        </div>
    </div>
</footer>

<script>
'use strict';
/* ── DATA (gerado pelo Python a partir do CSV) ── */
const DATA = {data_json};

const CAT_ORDER = [
    'Plataformas e Mobilização','Conversa e Diálogo','Informação e Persuasão',
    'Dados e Mapas','Materiais de Comunicação','Jogos','Abstenção e Virada'
];
const CAT_ICONS = {{
    'Plataformas e Mobilização':'📡','Conversa e Diálogo':'💬',
    'Informação e Persuasão':'📊','Dados e Mapas':'🗺️',
    'Materiais de Comunicação':'📢','Jogos':'🎮','Abstenção e Virada':'🔄'
}};
const CAT_COLORS = {{
    'Plataformas e Mobilização':'#C3090A','Conversa e Diálogo':'#0270AA',
    'Informação e Persuasão':'#087A23','Dados e Mapas':'#048ED6',
    'Materiais de Comunicação':'#A00708','Jogos':'#B8A000','Abstenção e Virada':'#0B912A'
}};

/* build ordered category list */
const found = [...new Set(DATA.map(r => r.cat))];
const CATS = [...CAT_ORDER.filter(c => found.includes(c)), ...found.filter(c => !CAT_ORDER.includes(c))];

let activeCat = 'TODAS';
let query     = '';
let toastTid;
let cardId    = 0;

/* ── DOM REFS ── */
const hub      = document.getElementById('hub');
const pillsRow = document.getElementById('pillsRow');
const srch     = document.getElementById('searchInput');
const clearBtn = document.getElementById('clearBtn');
const empty    = document.getElementById('empty');
const fltBar   = document.getElementById('fltBar');
const fltTxt   = document.getElementById('fltTxt');
const toast    = document.getElementById('toast');
const toastMsg = document.getElementById('toastMsg');
const scrollTop= document.getElementById('scrollTop');

/* ── PILLS ── */
function renderPills() {{
    pillsRow.innerHTML = '';
    pillsRow.appendChild(makePill('Todas as Categorias', DATA.length, 'TODAS'));
    CATS.forEach(c => {{
        const n = DATA.filter(r => r.cat === c).length;
        pillsRow.appendChild(makePill(c, n, c));
    }});
}}
function makePill(lbl, n, val) {{
    const btn = document.createElement('button');
    btn.className = 'pill' + (activeCat === val ? ' active' : '');
    btn.setAttribute('aria-pressed', activeCat === val ? 'true' : 'false');
    const ico = CAT_ICONS[val] ? `<span aria-hidden="true">${{CAT_ICONS[val]}}</span>` : '';
    btn.innerHTML = `${{ico}} ${{esc(lbl)}} <span class="pill-n">${{n}}</span>`;
    btn.addEventListener('click', () => {{ activeCat = val; renderPills(); renderHub(); filterStatus(); }});
    return btn;
}}

/* ── RENDER HUB ── */
function renderHub() {{
    hub.innerHTML = '';
    const q = query.toLowerCase().trim();
    const filtered = DATA.filter(r => {{
        const mc = activeCat === 'TODAS' || r.cat === activeCat;
        const mq = !q || r.nome.toLowerCase().includes(q) || r.desc.toLowerCase().includes(q)
                     || r.link.toLowerCase().includes(q) || r.cat.toLowerCase().includes(q);
        return mc && mq;
    }});
    if (!filtered.length) {{ empty.classList.add('on'); return; }}
    empty.classList.remove('on');
    const cats = activeCat === 'TODAS' ? CATS : [activeCat];
    cats.forEach(c => {{
        const items = filtered.filter(r => r.cat === c);
        if (!items.length) return;
        hub.appendChild(buildSection(c, items));
    }});
}}

/* ── SECTION ── */
function buildSection(cat, items) {{
    const sec = document.createElement('section');
    sec.className = 'cat-section';
    const color = CAT_COLORS[cat] || '#C3090A';
    const icon  = CAT_ICONS[cat] || '';
    const hdr = document.createElement('div');
    hdr.className = 'cat-hdr';
    hdr.innerHTML = `
        <div class="cat-bar" style="background:${{color}}" aria-hidden="true"></div>
        <h2><span aria-hidden="true">${{icon}}</span> ${{esc(cat)}}</h2>
        <span class="cat-cnt">${{items.length}} ${{items.length===1?'iniciativa':'iniciativas'}}</span>
    `;
    sec.appendChild(hdr);
    const grid = document.createElement('div');
    grid.className = 'grid';
    items.forEach(item => grid.appendChild(buildCard(item)));
    sec.appendChild(grid);
    return sec;
}}

/* ── CARD ── */
function buildCard(item) {{
    cardId++;
    const id = `acc-${{cardId}}`;
    const url = /^https?:\/\//i.test(item.link) ? item.link : 'https://' + item.link;
    const domain = (item.link || '').replace(/^https?:\/\//i,'').split('/')[0];
    const art = document.createElement('article');
    art.className = 'card';
    art.innerHTML = `
        <div class="card-top">
            <span class="cat-badge">${{esc(item.cat)}}</span>
            <span class="card-domain" title="${{escA(item.link)}}">${{esc(domain)}}</span>
        </div>
        <h3 class="card-title">${{esc(item.nome)}}</h3>
        <div class="acc-wrap">
            <button class="acc-btn" id="${{id}}-btn" aria-expanded="false" aria-controls="${{id}}" type="button">
                <span>Detalhes</span>
                <svg class="chevron" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 9l-7 7-7-7"/>
                </svg>
            </button>
            <div class="acc-body" id="${{id}}" role="region" aria-labelledby="${{id}}-btn">
                <div class="acc-inner">
                    <p class="acc-desc">${{esc(item.desc) || 'Sem descrição disponível.'}}</p>
                </div>
            </div>
        </div>
        <div class="actions">
            <a href="${{escA(url)}}" target="_blank" rel="noopener noreferrer" class="btn-p" aria-label="Acessar ${{escA(item.nome)}} (abre em nova aba)">
                <span>Acessar</span>
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                </svg>
            </a>
            <button class="btn-o" type="button" aria-label="Copiar link de ${{escA(item.nome)}}" title="Copiar link" data-url="${{escA(url)}}" data-nome="${{escA(item.nome)}}">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                </svg>
                <span class="lbl">Copiar</span>
            </button>
        </div>
    `;
    /* accordion */
    const trigger = art.querySelector('.acc-btn');
    const body    = art.querySelector('.acc-body');
    trigger.addEventListener('click', () => {{
        const exp = trigger.getAttribute('aria-expanded') === 'true';
        trigger.setAttribute('aria-expanded', String(!exp));
        body.classList.toggle('open', !exp);
    }});
    /* copy */
    const copyBtn = art.querySelector('.btn-o');
    copyBtn.addEventListener('click', () => copyLink(copyBtn.dataset.url, copyBtn.dataset.nome, copyBtn));
    return art;
}}

/* ── COPY ── */
function copyLink(url, nome, btn) {{
    const done = () => {{
        const orig = btn.innerHTML;
        btn.innerHTML = `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="14" height="14"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg><span class="lbl">Copiado!</span>`;
        btn.style.cssText = 'border-color:#087A23;color:#087A23';
        setTimeout(() => {{ btn.innerHTML = orig; btn.style.cssText = ''; }}, 2000);
        toast_show(`Link de "${{nome}}" copiado!`);
    }};
    if (navigator.clipboard && window.isSecureContext) {{
        navigator.clipboard.writeText(url).then(done).catch(() => fbCopy(url, done));
    }} else {{ fbCopy(url, done); }}
}}
function fbCopy(text, cb) {{
    const ta = document.createElement('textarea');
    ta.value = text;
    Object.assign(ta.style, {{position:'fixed',top:0,left:0,opacity:0}});
    document.body.appendChild(ta); ta.focus(); ta.select();
    try {{ document.execCommand('copy'); cb(); }} catch{{}}
    document.body.removeChild(ta);
}}

/* ── TOAST ── */
function toast_show(msg) {{
    toastMsg.textContent = msg;
    toast.classList.add('on');
    clearTimeout(toastTid);
    toastTid = setTimeout(() => toast.classList.remove('on'), 3000);
}}

/* ── FILTER STATUS ── */
function filterStatus() {{
    const hasQ = query.trim().length > 0;
    const hasC = activeCat !== 'TODAS';
    if (hasQ || hasC) {{
        fltBar.classList.add('on');
        const parts = [];
        if (hasC) parts.push(`Categoria: "${{activeCat}}"`);
        if (hasQ) parts.push(`Busca: "${{query}}"`);
        fltTxt.textContent = `Filtros ativos — ${{parts.join(' | ')}}`;
    }} else {{ fltBar.classList.remove('on'); }}
}}

/* ── RESET ── */
function reset() {{
    activeCat = 'TODAS'; query = '';
    srch.value = ''; clearBtn.style.display = 'none';
    renderPills(); renderHub(); filterStatus(); srch.focus();
}}
window.reset = reset;

/* ── SEARCH ── */
srch.addEventListener('input', e => {{
    query = e.target.value;
    clearBtn.style.display = query ? 'inline-flex' : 'none';
    renderHub(); filterStatus();
}});
clearBtn.addEventListener('click', () => {{
    srch.value = ''; query = ''; clearBtn.style.display = 'none';
    renderHub(); filterStatus(); srch.focus();
}});

/* ── SCROLL TOP ── */
window.addEventListener('scroll', () => {{
    scrollTop.classList.toggle('on', window.scrollY > 400);
}}, {{passive:true}});
scrollTop.addEventListener('click', () => window.scrollTo({{top:0,behavior:'smooth'}}));

/* ── ESCAPE HELPERS ── */
function esc(s)  {{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}
function escA(s) {{ return String(s||'').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }}

/* ── INIT ── */
renderPills();
renderHub();
</script>
</body>
</html>"""


# ─── Geração e escrita do HTML ────────────────────────────────────
def generate():
    if not os.path.exists(CSV_FILE):
        print(f"  ✗ CSV não encontrado: {CSV_FILE}")
        sys.exit(1)

    rows = read_csv(CSV_FILE)
    dt   = datetime.now().strftime('%d/%m/%Y às %H:%M')
    html = build_html(rows, dt)

    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n  ✓ HTML gerado: {HTML_OUT}")
    print(f"    {len(rows)} iniciativas | {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ─── Servidor local ────────────────────────────────────────────────
def serve():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=DIR, **kw)
        def log_message(self, f, *a):
            if '200' in str(a): print(f"  ✓ {a[0]}")

    def open_browser():
        time.sleep(0.8)
        url = f"http://localhost:{PORT}/hub_de_iniciativas_digitais.html"
        webbrowser.open(url)
        print(f"\n  🌐 Abrindo: {url}")

    print(f"\n  📡 Servidor: http://localhost:{PORT}")
    print("  Pressione Ctrl+C para encerrar.\n")
    threading.Thread(target=open_browser, daemon=True).start()

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n  ✋ Encerrado.\n")


# ─── Entry point ───────────────────────────────────────────────────
if __name__ == '__main__':
    os.chdir(DIR)
    print("\n" + "=" * 55)
    print("  HUB DE INICIATIVAS DIGITAIS — Gerador + Servidor")
    print("=" * 55)
    generate()
    serve()
