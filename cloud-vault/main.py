import os
import hashlib
import json
from datetime import datetime, timedelta, timezone
import boto3
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Header
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CloudVault — Zero-Trust Serverless Storage Console")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
VAULT_PASSCODE = os.getenv("VAULT_PASSCODE", "BNMIT2026")
LAMBDA_LOG_GROUP = os.getenv("LAMBDA_LOG_GROUP", "/aws/lambda/cloudvault-s3-auditor")

MAX_FILE_SIZE_MB = 25
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".msi", ".vbs", ".scr", ".ps1"}

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)

logs_client = boto3.client(
    "logs",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)


def verify_passcode(x_vault_passcode: str | None):
    if not x_vault_passcode or x_vault_passcode != VAULT_PASSCODE:
        raise HTTPException(
            status_code=401,
            detail="Vault Locked: Enter valid Vault Passcode (default: BNMIT2026) to authorize write/delete operations.",
        )


@app.get("/", response_class=HTMLResponse)
def home():
    return r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>CloudVault | Zero-Trust Serverless Cloud Storage</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-base: #060913;
                --bg-card: rgba(15, 23, 42, 0.84);
                --bg-hover: rgba(30, 41, 59, 0.72);
                --border: rgba(148, 163, 184, 0.14);
                --border-glow: rgba(99, 102, 241, 0.48);
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --accent: #6366f1;
                --accent-cyan: #06b6d4;
                --success: #10b981;
                --danger: #ef4444;
                --warning: #f59e0b;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; }

            body {
                font-family: 'Inter', -apple-system, sans-serif;
                background-color: var(--bg-base);
                color: var(--text-primary);
                min-height: 100vh;
                background-image:
                    radial-gradient(circle at 12% 8%, rgba(99, 102, 241, 0.18), transparent 36%),
                    radial-gradient(circle at 88% 12%, rgba(6, 182, 212, 0.14), transparent 34%),
                    linear-gradient(rgba(148, 163, 184, 0.035) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(148, 163, 184, 0.035) 1px, transparent 1px);
                background-size: 100% 100%, 100% 100%, 34px 34px, 34px 34px;
            }

            .navbar {
                position: sticky;
                top: 0;
                z-index: 50;
                backdrop-filter: blur(16px);
                background: rgba(6, 9, 19, 0.82);
                border-bottom: 1px solid var(--border);
            }

            .nav-inner {
                max-width: 1220px;
                margin: 0 auto;
                padding: 13px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                flex-wrap: wrap;
            }

            .brand { display: flex; align-items: center; gap: 12px; }

            .brand-icon {
                width: 38px; height: 38px; border-radius: 10px;
                background: linear-gradient(135deg, var(--accent), var(--accent-cyan));
                display: grid; place-items: center;
                box-shadow: 0 0 24px rgba(99, 102, 241, 0.45);
            }

            .brand-title { font-size: 1.12rem; font-weight: 700; letter-spacing: -0.02em; }
            .brand-sub { font-size: 0.74rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }

            .nav-pills { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }

            .status-pill {
                display: inline-flex; align-items: center; gap: 8px;
                padding: 6px 12px; border-radius: 999px;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.28);
                color: #6ee7b7; font-size: 0.76rem;
                font-family: 'JetBrains Mono', monospace;
            }

            .pulse-dot {
                width: 8px; height: 8px; border-radius: 50%;
                background: var(--success);
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
                100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }

            .vault-btn {
                display: inline-flex; align-items: center; gap: 6px;
                padding: 6px 13px; border-radius: 999px;
                font-size: 0.78rem; font-weight: 600; cursor: pointer;
                border: 1px solid rgba(245, 158, 11, 0.4);
                background: rgba(245, 158, 11, 0.12);
                color: #fcd34d;
                transition: all 0.2s ease;
            }

            .vault-btn.unlocked {
                border-color: rgba(16, 185, 129, 0.4);
                background: rgba(16, 185, 129, 0.12);
                color: #6ee7b7;
            }

            .nav-link {
                color: var(--text-secondary); text-decoration: none;
                font-size: 0.8rem; font-weight: 500;
                padding: 6px 11px; border-radius: 8px;
                border: 1px solid var(--border);
                background: rgba(15, 23, 42, 0.55);
                transition: all 0.2s ease;
            }

            .nav-link:hover { color: var(--text-primary); border-color: var(--border-glow); }

            .container { max-width: 1220px; margin: 0 auto; padding: 24px 24px 60px; }

            .view-tabs {
                display: inline-flex; background: rgba(15, 23, 42, 0.85);
                border: 1px solid var(--border); border-radius: 12px;
                padding: 4px; margin-bottom: 22px; flex-wrap: wrap; gap: 4px;
            }

            .tab-btn {
                border: none; background: transparent; color: var(--text-secondary);
                padding: 9px 16px; border-radius: 9px; font-size: 0.84rem;
                font-weight: 600; cursor: pointer; transition: all 0.2s ease;
            }

            .tab-btn.active {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.28), rgba(6, 182, 212, 0.22));
                color: var(--text-primary);
                border: 1px solid rgba(99, 102, 241, 0.38);
            }

            .kpi-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px; margin-bottom: 22px;
            }

            .kpi-card {
                background: var(--bg-card); border: 1px solid var(--border);
                border-radius: 14px; padding: 17px 19px; backdrop-filter: blur(12px);
            }

            .kpi-label { font-size: 0.73rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-secondary); margin-bottom: 6px; }
            .kpi-value { font-size: 1.38rem; font-weight: 700; letter-spacing: -0.02em; }
            .kpi-meta { margin-top: 5px; font-size: 0.74rem; font-family: 'JetBrains Mono', monospace; color: var(--accent-cyan); }

            .dashboard-grid {
                display: grid; grid-template-columns: 375px 1fr;
                gap: 20px; align-items: start;
            }

            @media (max-width: 960px) { .dashboard-grid { grid-template-columns: 1fr; } }

            .panel {
                background: var(--bg-card); border: 1px solid var(--border);
                border-radius: 16px; padding: 20px; backdrop-filter: blur(14px);
                box-shadow: 0 20px 45px -20px rgba(0, 0, 0, 0.7);
            }

            .panel-header {
                display: flex; align-items: center; justify-content: space-between;
                margin-bottom: 15px; gap: 10px; flex-wrap: wrap;
            }

            .panel-title { font-size: 0.98rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }

            .guardrail-box {
                background: rgba(99, 102, 241, 0.07);
                border: 1px solid rgba(99, 102, 241, 0.24);
                border-radius: 10px; padding: 10px 12px;
                margin-bottom: 14px; font-size: 0.76rem; color: var(--text-secondary);
                line-height: 1.45;
            }

            .guardrail-box strong { color: #a5b4fc; }

            .dropzone {
                border: 2px dashed rgba(99, 102, 241, 0.38); border-radius: 14px;
                padding: 28px 18px; text-align: center;
                background: rgba(99, 102, 241, 0.04); cursor: pointer;
                transition: all 0.2s ease;
            }

            .dropzone:hover, .dropzone.dragover {
                border-color: var(--accent-cyan); background: rgba(6, 182, 212, 0.08);
            }

            .drop-title { font-size: 0.92rem; font-weight: 600; margin-bottom: 4px; }
            .drop-hint { font-size: 0.78rem; color: var(--text-secondary); }

            .file-preview {
                display: none; margin-top: 12px; padding: 11px 13px; border-radius: 10px;
                background: rgba(15, 23, 42, 0.92); border: 1px solid var(--border-glow);
                align-items: center; justify-content: space-between; gap: 10px;
            }

            .file-preview.visible { display: flex; }
            .file-preview-name { font-size: 0.84rem; font-weight: 600; word-break: break-all; }
            .file-preview-size { font-size: 0.73rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }

            .clear-btn { background: transparent; border: none; color: var(--text-secondary); cursor: pointer; font-size: 0.8rem; }
            .clear-btn:hover { color: var(--danger); }

            .progress-wrap { display: none; margin-top: 12px; }
            .progress-wrap.visible { display: block; }
            .progress-bar-bg { width: 100%; height: 6px; border-radius: 999px; background: rgba(148, 163, 184, 0.16); overflow: hidden; }
            .progress-bar-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--accent), var(--accent-cyan)); transition: width 0.2s ease; }
            .progress-label { margin-top: 5px; font-size: 0.73rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; text-align: right; }

            .btn-primary {
                width: 100%; margin-top: 14px; padding: 11px 16px; border: none; border-radius: 10px;
                font-size: 0.88rem; font-weight: 600; color: #fff;
                background: linear-gradient(135deg, var(--accent), #4f46e5);
                box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.65);
                cursor: pointer; transition: all 0.2s ease;
            }

            .btn-primary:hover:not(:disabled) { transform: translateY(-1px); }
            .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

            .toolbar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

            .search-input {
                background: rgba(6, 9, 19, 0.8); border: 1px solid var(--border);
                border-radius: 9px; padding: 7px 11px; color: var(--text-primary);
                font-size: 0.82rem; min-width: 185px; outline: none;
            }

            .search-input:focus { border-color: var(--accent); }

            .btn-icon {
                background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border);
                color: var(--text-secondary); border-radius: 9px; padding: 7px 11px;
                font-size: 0.8rem; cursor: pointer;
            }

            .btn-icon:hover { color: var(--text-primary); border-color: var(--border-glow); }

            .table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--border); }
            table { width: 100%; border-collapse: collapse; text-align: left; }
            th {
                background: rgba(6, 9, 19, 0.75); padding: 11px 12px; font-size: 0.72rem;
                text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary);
                border-bottom: 1px solid var(--border);
            }
            td { padding: 12px; font-size: 0.84rem; border-bottom: 1px solid rgba(148, 163, 184, 0.08); vertical-align: middle; }
            tbody tr:hover { background: rgba(30, 41, 59, 0.45); }

            .ext-badge {
                display: inline-block; padding: 2px 6px; border-radius: 5px;
                font-size: 0.68rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
                background: rgba(99, 102, 241, 0.2); color: #a5b4fc; margin-right: 6px;
            }

            .hash-pill {
                display: inline-block; padding: 3px 7px; border-radius: 6px;
                font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
                background: rgba(16, 185, 129, 0.12); color: #6ee7b7;
                border: 1px solid rgba(16, 185, 129, 0.25);
            }

            .hash-pill.unverified {
                background: rgba(245, 158, 11, 0.12); color: #fcd34d;
                border-color: rgba(245, 158, 11, 0.25);
            }

            .mono { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-secondary); }
            .action-group { display: inline-flex; gap: 5px; flex-wrap: wrap; justify-content: flex-end; }

            .btn-sm {
                padding: 5px 9px; border-radius: 7px; font-size: 0.75rem; font-weight: 500;
                border: 1px solid var(--border); background: rgba(15, 23, 42, 0.95);
                color: var(--text-primary); cursor: pointer; transition: all 0.15s ease;
            }

            .btn-sm:hover { border-color: var(--accent-cyan); color: var(--accent-cyan); }
            .btn-sm.verify:hover { border-color: var(--success); color: #6ee7b7; }
            .btn-sm.danger:hover { border-color: var(--danger); color: #fca5a5; }

            .empty-state { padding: 36px 20px; text-align: center; color: var(--text-secondary); font-size: 0.86rem; }

            /* CloudWatch Terminal Feed */
            .cw-terminal {
                background: #03060d; border: 1px solid rgba(6, 182, 212, 0.28);
                border-radius: 12px; padding: 16px; font-family: 'JetBrains Mono', monospace;
                font-size: 0.79rem; max-height: 480px; overflow-y: auto;
            }

            .cw-entry {
                padding: 10px 12px; border-radius: 8px;
                background: rgba(15, 23, 42, 0.65);
                border-left: 3px solid var(--accent-cyan);
                margin-bottom: 10px; line-height: 1.5;
            }

            .cw-entry.delete-ev { border-left-color: var(--danger); }
            .cw-meta { color: var(--text-secondary); font-size: 0.72rem; margin-bottom: 4px; }
            .cw-event { color: #38bdf8; font-weight: 600; }
            .cw-entry.delete-ev .cw-event { color: #fca5a5; }

            /* Architecture Grid */
            .flow-diagram {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 14px; margin-bottom: 20px;
            }

            .flow-node {
                background: rgba(6, 9, 19, 0.78); border: 1px solid var(--border-glow);
                border-radius: 12px; padding: 15px;
            }

            .flow-tag { font-size: 0.69rem; font-family: 'JetBrains Mono', monospace; color: var(--accent-cyan); margin-bottom: 5px; }
            .flow-title { font-size: 0.94rem; font-weight: 700; margin-bottom: 5px; }
            .flow-desc { font-size: 0.79rem; color: var(--text-secondary); line-height: 1.45; }

            /* Modal */
            .modal-backdrop {
                display: none; position: fixed; inset: 0; z-index: 90;
                background: rgba(2, 6, 23, 0.78); backdrop-filter: blur(8px);
                place-items: center; padding: 20px;
            }

            .modal-backdrop.open { display: grid; }

            .modal-card {
                width: 100%; max-width: 440px; background: #0f172a;
                border: 1px solid var(--border-glow); border-radius: 16px;
                padding: 22px; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8);
            }

            .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
            .modal-title { font-size: 1rem; font-weight: 700; }
            .close-modal { background: none; border: none; color: var(--text-secondary); font-size: 1.2rem; cursor: pointer; }

            .expiry-pills { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0; }
            .exp-btn {
                padding: 8px; border-radius: 8px; border: 1px solid var(--border);
                background: rgba(6, 9, 19, 0.8); color: var(--text-secondary);
                font-size: 0.78rem; font-weight: 600; cursor: pointer;
            }
            .exp-btn.active { border-color: var(--accent-cyan); color: var(--text-primary); background: rgba(6, 182, 212, 0.16); }

            .share-url-box {
                width: 100%; padding: 9px 11px; border-radius: 8px;
                background: #060913; border: 1px solid var(--border);
                color: #a5b4fc; font-family: 'JetBrains Mono', monospace;
                font-size: 0.74rem; margin: 10px 0;
            }

            .qr-wrap { text-align: center; margin: 12px 0; }
            .qr-wrap img { border-radius: 10px; border: 4px solid #fff; width: 150px; height: 150px; }
            .countdown-badge {
                display: inline-block; padding: 4px 10px; border-radius: 999px;
                background: rgba(245, 158, 11, 0.15); color: #fcd34d;
                font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;
            }

            .toast {
                position: fixed; bottom: 22px; right: 22px; z-index: 120;
                padding: 12px 17px; border-radius: 12px;
                background: rgba(15, 23, 42, 0.97); border: 1px solid var(--border-glow);
                color: var(--text-primary); font-size: 0.84rem;
                box-shadow: 0 18px 36px rgba(0, 0, 0, 0.7);
                transform: translateY(130%); opacity: 0; transition: all 0.25s ease;
            }
            .toast.show { transform: translateY(0); opacity: 1; }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-inner">
                <div class="brand">
                    <div class="brand-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="brand-title">CloudVault Zero-Trust Console</div>
                        <div class="brand-sub">FastAPI • Docker • EC2 • S3 • Lambda • CloudWatch</div>
                    </div>
                </div>

                <div class="nav-pills">
                    <button type="button" class="vault-btn" id="vaultLockBtn" onclick="toggleVaultLock()">
                        🔒 Vault Locked (Click to Unlock)
                    </button>
                    <div class="status-pill">
                        <span class="pulse-dot"></span>
                        <span id="statusText">Connecting to AWS...</span>
                    </div>
                    <a class="nav-link" href="/docs" target="_blank">REST API</a>
                </div>
            </div>
        </nav>

        <main class="container">
            <div class="view-tabs">
                <button class="tab-btn active" id="tabConsole" onclick="switchTab('console')">Zero-Trust Storage Vault</button>
                <button class="tab-btn" id="tabLogs" onclick="switchTab('logs')">⚡ Live Lambda & CloudWatch Logs</button>
                <button class="tab-btn" id="tabArch" onclick="switchTab('arch')">Event-Driven Architecture</button>
            </div>

            <!-- TAB 1: STORAGE VAULT -->
            <section id="viewConsole">
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Protected S3 Objects</div>
                        <div class="kpi-value" id="kpiCount">—</div>
                        <div class="kpi-meta" id="kpiBucket">Bucket: loading...</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Cryptographic Integrity</div>
                        <div class="kpi-value">SHA-256</div>
                        <div class="kpi-meta">End-to-End Checksum Metadata</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Serverless Event Trigger</div>
                        <div class="kpi-value">AWS Lambda</div>
                        <div class="kpi-meta">S3 Event → CloudWatch Audit</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Access Governance</div>
                        <div class="kpi-value" id="kpiAccessMode">Read-Only</div>
                        <div class="kpi-meta">Non-IAM Passcode + Presigned URLs</div>
                    </div>
                </div>

                <div class="dashboard-grid">
                    <!-- Upload Panel -->
                    <div class="panel">
                        <div class="panel-header">
                            <div class="panel-title">Upload With Policy Guardrails</div>
                        </div>

                        <div class="guardrail-box">
                            <strong>Active Policy Engine:</strong> Max <strong>25 MB</strong> per object • Blocks executable binaries (<code>.exe</code>, <code>.sh</code>, <code>.bat</code>) • Auto-computes <strong>SHA-256</strong> hash & triggers <strong>AWS Lambda</strong> audit log.
                        </div>

                        <div class="dropzone" id="dropzone">
                            <div class="drop-title">Drop file here or click to select</div>
                            <div class="drop-hint">Requires unlocked Vault Passcode (Default: BNMIT2026)</div>
                            <input type="file" id="fileInput" hidden />
                        </div>

                        <div class="file-preview" id="filePreview">
                            <div>
                                <div class="file-preview-name" id="previewName"></div>
                                <div class="file-preview-size" id="previewSize"></div>
                            </div>
                            <button type="button" class="clear-btn" onclick="clearFile()">Remove</button>
                        </div>

                        <div class="progress-wrap" id="progressWrap">
                            <div class="progress-bar-bg"><div class="progress-bar-fill" id="progressFill"></div></div>
                            <div class="progress-label" id="progressLabel">Hashing & Streaming... 0%</div>
                        </div>

                        <button type="button" class="btn-primary" id="uploadBtn" onclick="uploadSelectedFile()" disabled>
                            Hash & Deploy to AWS S3
                        </button>
                    </div>

                    <!-- Bucket Explorer -->
                    <div class="panel">
                        <div class="panel-header">
                            <div class="panel-title">Private S3 Vault Objects</div>
                            <div class="toolbar">
                                <input type="text" class="search-input" id="searchInput" placeholder="Filter objects..." oninput="renderFiles()" />
                                <button type="button" class="btn-icon" onclick="loadFiles()">↻ Refresh</button>
                            </div>
                        </div>

                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Object Key</th>
                                        <th>SHA-256 Fingerprint</th>
                                        <th>Size</th>
                                        <th style="text-align: right;">Zero-Trust Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="filesTableBody">
                                    <tr><td colspan="4" class="empty-state">Loading encrypted vault inventory...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            <!-- TAB 2: LIVE LAMBDA + CLOUDWATCH AUDIT STREAM -->
            <section id="viewLogs" style="display:none;">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">⚡ Live AWS Lambda Execution Logs (Amazon CloudWatch)</div>
                        <div class="toolbar">
                            <span class="mono" id="logGroupLabel">/aws/lambda/cloudvault-s3-auditor</span>
                            <button type="button" class="btn-icon" onclick="loadCloudWatchLogs()">↻ Fetch Latest Logs</button>
                        </div>
                    </div>
                    <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 14px;">
                        Every S3 <code>ObjectCreated</code> or <code>ObjectRemoved</code> event asynchronously triggers <strong>AWS Lambda</strong>, which inspects SHA-256 metadata and streams structured audit events into <strong>CloudWatch Logs</strong>.
                    </p>
                    <div class="cw-terminal" id="cwTerminal">
                        <div class="empty-state">Click "Fetch Latest Logs" or upload a file to stream CloudWatch events...</div>
                    </div>
                </div>
            </section>

            <!-- TAB 3: ARCHITECTURE -->
            <section id="viewArch" style="display:none;">
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">Why CloudVault Beats Raw AWS Console Access</div>
                    </div>
                    <div class="flow-diagram">
                        <div class="flow-node">
                            <div class="flow-tag">1. ZERO-TRUST GATEWAY</div>
                            <div class="flow-title">FastAPI + Docker (EC2)</div>
                            <div class="flow-desc">End users never receive AWS Console logins or IAM keys. FastAPI enforces file-type guardrails, passcode locks, and SHA-256 hashing before touching S3.</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">2. PRIVATE OBJECT STORE</div>
                            <div class="flow-title">Amazon S3 (ap-south-1)</div>
                            <div class="flow-desc">100% private bucket storing custom <code>x-amz-meta-sha256</code> fingerprints. External sharing uses self-destructing Presigned URLs (1 min to 24 hrs).</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">3. EVENT-DRIVEN COMPUTE</div>
                            <div class="flow-title">AWS Lambda Trigger</div>
                            <div class="flow-desc">S3 Event Notifications automatically invoke <code>cloudvault-s3-auditor</code> on every upload/delete—catching even direct AWS Console changes.</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">4. OBSERVABILITY & CI/CD</div>
                            <div class="flow-title">CloudWatch + GitHub Actions</div>
                            <div class="flow-desc">Lambda records immutable JSON audit logs in CloudWatch, while GitHub Actions automates Docker container builds on every commit.</div>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <!-- Self-Destructing Share Link & QR Modal -->
        <div class="modal-backdrop" id="shareModal">
            <div class="modal-card">
                <div class="modal-header">
                    <div class="modal-title">Zero-Trust Self-Destructing Share Link</div>
                    <button class="close-modal" onclick="closeShareModal()">×</button>
                </div>
                <div style="font-size: 0.82rem; color: var(--text-secondary);">
                    Target Object: <strong id="shareFileName" style="color: var(--text-primary);"></strong>
                </div>
                <div class="expiry-pills">
                    <button class="exp-btn active" onclick="selectExpiry(60, this)">1 Min</button>
                    <button class="exp-btn" onclick="selectExpiry(600, this)">10 Mins</button>
                    <button class="exp-btn" onclick="selectExpiry(3600, this)">1 Hour</button>
                    <button class="exp-btn" onclick="selectExpiry(86400, this)">24 Hours</button>
                </div>
                <div style="text-align:center;">
                    <span class="countdown-badge" id="expiryCountdown">Link expires in 01:00</span>
                </div>
                <input type="text" class="share-url-box" id="shareUrlInput" readonly />
                <div class="qr-wrap">
                    <img id="shareQrImg" alt="Presigned URL QR Code" />
                    <div style="font-size: 0.72rem; color: var(--text-secondary); margin-top: 6px;">
                        Scan with mobile camera to open directly from private S3
                    </div>
                </div>
                <div style="display:flex; gap:8px; margin-top:12px;">
                    <button class="btn-primary" style="margin-top:0;" onclick="copyShareUrl()">Copy Presigned URL</button>
                    <button class="btn-icon" onclick="openShareUrl()">Open ↗</button>
                </div>
            </div>
        </div>

        <div class="toast" id="toast"></div>

        <script>
            let allFiles = [];
            let selectedFile = null;
            let vaultPasscode = sessionStorage.getItem('vaultPasscode') || '';
            let currentShareKey = '';
            let countdownTimer = null;

            function updateVaultUI() {
                const btn = document.getElementById('vaultLockBtn');
                const mode = document.getElementById('kpiAccessMode');
                if (vaultPasscode) {
                    btn.textContent = '🔓 Vault Unlocked (Admin Session)';
                    btn.classList.add('unlocked');
                    mode.textContent = 'Unlocked (Read/Write)';
                } else {
                    btn.textContent = '🔒 Vault Locked (Click to Unlock)';
                    btn.classList.remove('unlocked');
                    mode.textContent = 'Read-Only (Locked)';
                }
            }

            function toggleVaultLock() {
                if (vaultPasscode) {
                    vaultPasscode = '';
                    sessionStorage.removeItem('vaultPasscode');
                    showToast('Vault locked. Write & delete actions disabled.');
                } else {
                    const code = prompt('Enter Vault Passcode to authorize uploads & deletions (Demo Passcode: BNMIT2026):');
                    if (code) {
                        vaultPasscode = code.trim();
                        sessionStorage.setItem('vaultPasscode', vaultPasscode);
                        showToast('Vault unlocked for this browser session.');
                    }
                }
                updateVaultUI();
            }

            function switchTab(tab) {
                document.getElementById('viewConsole').style.display = tab === 'console' ? 'block' : 'none';
                document.getElementById('viewLogs').style.display = tab === 'logs' ? 'block' : 'none';
                document.getElementById('viewArch').style.display = tab === 'arch' ? 'block' : 'none';
                document.getElementById('tabConsole').classList.toggle('active', tab === 'console');
                document.getElementById('tabLogs').classList.toggle('active', tab === 'logs');
                document.getElementById('tabArch').classList.toggle('active', tab === 'arch');
                if (tab === 'logs') loadCloudWatchLogs();
            }

            function showToast(msg, isError = false) {
                const t = document.getElementById('toast');
                t.textContent = msg;
                t.style.borderColor = isError ? 'rgba(239, 68, 68, 0.65)' : 'rgba(16, 185, 129, 0.65)';
                t.classList.add('show');
                setTimeout(() => t.classList.remove('show'), 3800);
            }

            function formatBytes(bytes) {
                if (!bytes) return '0 B';
                const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }

            function escapeHtml(str) {
                return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
            }

            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('dragover'); });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
            dropzone.addEventListener('drop', e => {
                e.preventDefault(); dropzone.classList.remove('dragover');
                if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
            });
            fileInput.addEventListener('change', () => { if (fileInput.files.length) setFile(fileInput.files[0]); });

            function setFile(file) {
                selectedFile = file;
                document.getElementById('previewName').textContent = file.name;
                document.getElementById('previewSize').textContent = formatBytes(file.size);
                document.getElementById('filePreview').classList.add('visible');
                document.getElementById('uploadBtn').disabled = false;
            }

            function clearFile() {
                selectedFile = null; fileInput.value = '';
                document.getElementById('filePreview').classList.remove('visible');
                document.getElementById('uploadBtn').disabled = true;
            }

            function uploadSelectedFile() {
                if (!selectedFile) return;
                if (!vaultPasscode) {
                    toggleVaultLock();
                    if (!vaultPasscode) return;
                }

                const btn = document.getElementById('uploadBtn');
                const progressWrap = document.getElementById('progressWrap');
                const progressFill = document.getElementById('progressFill');
                const progressLabel = document.getElementById('progressLabel');

                btn.disabled = true;
                progressWrap.classList.add('visible');
                progressFill.style.width = '20%';
                progressLabel.textContent = 'Computing SHA-256 & enforcing guardrails...';

                const formData = new FormData();
                formData.append('file', selectedFile);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload', true);
                xhr.setRequestHeader('X-Vault-Passcode', vaultPasscode);

                xhr.upload.onprogress = e => {
                    if (e.lengthComputable) {
                        const pct = Math.min(92, Math.round((e.loaded / e.total) * 100));
                        progressFill.style.width = pct + '%';
                        progressLabel.textContent = `Streaming to S3... ${pct}%`;
                    }
                };

                xhr.onload = () => {
                    progressFill.style.width = '100%';
                    if (xhr.status >= 200 && xhr.status < 300) {
                        const res = JSON.parse(xhr.responseText);
                        showToast(`Uploaded! SHA-256: ${res.sha256.slice(0, 12)}... (Lambda triggered)`);
                        clearFile();
                        loadFiles();
                    } else {
                        let msg = 'Upload blocked';
                        try { msg = JSON.parse(xhr.responseText).detail || msg; } catch (_) {}
                        if (xhr.status === 401) { vaultPasscode = ''; sessionStorage.removeItem('vaultPasscode'); updateVaultUI(); }
                        showToast(msg, true);
                        btn.disabled = false;
                    }
                    setTimeout(() => { progressWrap.classList.remove('visible'); progressFill.style.width = '0%'; }, 600);
                };

                xhr.onerror = () => { showToast('Network error', true); btn.disabled = false; };
                xhr.send(formData);
            }

            async function loadFiles() {
                try {
                    const res = await fetch('/files');
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Error loading files');
                    allFiles = data.files || [];
                    document.getElementById('statusText').textContent = `Connected • ${data.region}`;
                    document.getElementById('kpiCount').textContent = data.count;
                    document.getElementById('kpiBucket').textContent = `Bucket: ${data.bucket}`;
                    renderFiles();
                } catch (err) {
                    document.getElementById('statusText').textContent = 'AWS Connection Error';
                    document.getElementById('filesTableBody').innerHTML = `<tr><td colspan="4" class="empty-state" style="color:#fca5a5;">${escapeHtml(err.message)}</td></tr>`;
                }
            }

            function renderFiles() {
                const q = document.getElementById('searchInput').value.toLowerCase();
                const tbody = document.getElementById('filesTableBody');
                const filtered = allFiles.filter(f => f.key.toLowerCase().includes(q));

                if (!filtered.length) {
                    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No objects in vault. Unlock vault & upload a file.</td></tr>`;
                    return;
                }

                tbody.innerHTML = filtered.map(f => {
                    const ext = f.key.includes('.') ? f.key.split('.').pop().slice(0, 4).toUpperCase() : 'FILE';
                    const hasHash = f.sha256 && f.sha256 !== 'UNVERIFIED';
                    const hashBadge = hasHash
                        ? `<span class="hash-pill" title="${escapeHtml(f.sha256)}">SHA256: ${escapeHtml(f.sha256.slice(0, 12))}…</span>`
                        : `<span class="hash-pill unverified">Direct Console Upload</span>`;

                    return `
                        <tr>
                            <td><span class="ext-badge">${escapeHtml(ext)}</span><strong>${escapeHtml(f.key)}</strong></td>
                            <td>${hashBadge}</td>
                            <td class="mono">${formatBytes(f.size)}</td>
                            <td style="text-align:right;">
                                <div class="action-group">
                                    <button type="button" class="btn-sm verify" data-action="verify" data-key="${escapeHtml(f.key)}">Verify Hash</button>
                                    <button type="button" class="btn-sm" data-action="share" data-key="${escapeHtml(f.key)}">Share / QR</button>
                                    <button type="button" class="btn-sm danger" data-action="delete" data-key="${escapeHtml(f.key)}">Delete</button>
                                </div>
                            </td>
                        </tr>
                    `;
                }).join('');
            }

            document.getElementById('filesTableBody').addEventListener('click', (e) => {
                const btn = e.target.closest('button[data-action]');
                if (!btn) return;
                const action = btn.getAttribute('data-action');
                const key = btn.getAttribute('data-key');
                if (action === 'verify') verifyIntegrity(key);
                else if (action === 'share') openShareModal(key);
                else if (action === 'delete') deleteFile(key);
            });
            

            async function verifyIntegrity(key) {
                showToast(`Recomputing live SHA-256 from S3 stream for "${key}"...`);
                try {
                    const res = await fetch(`/verify?key=${encodeURIComponent(key)}`);
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Verification failed');
                    if (data.verified) {
                        showToast(`✅ INTEGRITY VERIFIED: Live S3 SHA-256 matches stored fingerprint (${data.computed_sha256.slice(0, 14)}...)`);
                    } else {
                        showToast(`⚠️ Unverified origin (uploaded outside CloudVault). Live SHA-256: ${data.computed_sha256.slice(0, 14)}...`, true);
                    }
                } catch (err) {
                    showToast(err.message, true);
                }
            }

            async function deleteFile(key) {
                if (!vaultPasscode) {
                    toggleVaultLock();
                    if (!vaultPasscode) return;
                }
                if (!confirm(`Permanently delete "${key}" from S3 and trigger Lambda removal log?`)) return;
                try {
                    const res = await fetch(`/delete?key=${encodeURIComponent(key)}`, {
                        method: 'DELETE',
                        headers: { 'X-Vault-Passcode': vaultPasscode }
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        if (res.status === 401) { vaultPasscode = ''; sessionStorage.removeItem('vaultPasscode'); updateVaultUI(); }
                        throw new Error(data.detail || 'Delete failed');
                    }
                    showToast(`Deleted "${key}" (Lambda audit event triggered)`);
                    loadFiles();
                } catch (err) {
                    showToast(err.message, true);
                }
            }

            /* Share Modal with Self-Destruct Timer & QR */
            function openShareModal(key) {
                currentShareKey = key;
                document.getElementById('shareFileName').textContent = key;
                document.getElementById('shareModal').classList.add('open');
                const btns = document.querySelectorAll('.exp-btn');
                btns.forEach(b => b.classList.remove('active'));
                btns[0].classList.add('active');
                generateShareLink(60);
            }

            function closeShareModal() {
                document.getElementById('shareModal').classList.remove('open');
                if (countdownTimer) clearInterval(countdownTimer);
            }

            function selectExpiry(seconds, btnEl) {
                document.querySelectorAll('.exp-btn').forEach(b => b.classList.remove('active'));
                btnEl.classList.add('active');
                generateShareLink(seconds);
            }

            async function generateShareLink(seconds) {
                try {
                    const res = await fetch(`/download?key=${encodeURIComponent(currentShareKey)}&expires=${seconds}`);
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Failed to generate presigned URL');
                    document.getElementById('shareUrlInput').value = data.url;
                    document.getElementById('shareQrImg').src = `https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(data.url)}`;
                    startCountdown(seconds);
                } catch (err) {
                    showToast(err.message, true);
                }
            }

            function startCountdown(seconds) {
                if (countdownTimer) clearInterval(countdownTimer);
                let remaining = seconds;
                const badge = document.getElementById('expiryCountdown');
                const tick = () => {
                    if (remaining <= 0) {
                        badge.textContent = 'EXPIRED — Presigned URL Self-Destructed';
                        clearInterval(countdownTimer);
                        return;
                    }
                    const mins = Math.floor(remaining / 60);
                    const secs = remaining % 60;
                    badge.textContent = `Self-destructs in ${String(mins).padStart(2,'0')}m ${String(secs).padStart(2,'0')}s`;
                    remaining--;
                };
                tick();
                countdownTimer = setInterval(tick, 1000);
            }

            function copyShareUrl() {
                const input = document.getElementById('shareUrlInput');
                input.select();
                navigator.clipboard.writeText(input.value);
                showToast('Time-bounded Presigned URL copied to clipboard');
            }

            function openShareUrl() {
                const url = document.getElementById('shareUrlInput').value;
                if (url) window.open(url, '_blank');
            }

            /* CloudWatch Logs Stream */
            async function loadCloudWatchLogs() {
                const terminal = document.getElementById('cwTerminal');
                terminal.innerHTML = `<div class="empty-state">Querying Amazon CloudWatch Logs via boto3...</div>`;
                try {
                    const res = await fetch('/logs');
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Failed to fetch CloudWatch logs');
                    document.getElementById('logGroupLabel').textContent = data.log_group;
                    if (!data.events.length) {
                        terminal.innerHTML = `<div class="empty-state">No Lambda audit events yet. Upload or delete a file in S3 and wait 3 seconds!</div>`;
                        return;
                    }
                    terminal.innerHTML = data.events.map(ev => {
                        const isDel = (ev.event || '').includes('Removed');
                        return `
                            <div class="cw-entry ${isDel ? 'delete-ev' : ''}">
                                <div class="cw-meta">${escapeHtml(ev.ingested_at)} • RequestId: ${escapeHtml(ev.request_id || 'N/A')} • IP: ${escapeHtml(ev.source_ip || 'N/A')}</div>
                                <div><span class="cw-event">[${escapeHtml(ev.event)}]</span> <strong>${escapeHtml(ev.key)}</strong> (${formatBytes(ev.size_bytes)})</div>
                                <div style="color:#a5b4fc; font-size:0.74rem; margin-top:3px;">Origin: ${escapeHtml(ev.origin)} | SHA-256: ${escapeHtml(ev.sha256)}</div>
                            </div>
                        `;
                    }).join('');
                } catch (err) {
                    terminal.innerHTML = `<div class="empty-state" style="color:#fca5a5;">${escapeHtml(err.message)}</div>`;
                }
            }

            updateVaultUI();
            loadFiles();
        </script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_vault_passcode: str | None = Header(default=None),
):
    verify_passcode(x_vault_passcode)
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Security Guardrail Blocked Upload: Executable extension '{ext}' is prohibited.",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Policy Guardrail Blocked Upload: File ({size_mb:.2f} MB) exceeds {MAX_FILE_SIZE_MB} MB limit.",
        )

    sha256_hash = hashlib.sha256(content).hexdigest()

    try:
        import io
        s3_client.upload_fileobj(
            io.BytesIO(content),
            S3_BUCKET,
            file.filename,
            ExtraArgs={
                "Metadata": {
                    "sha256": sha256_hash,
                    "source": "CLOUDVAULT_WEB_APP",
                }
            },
        )
        return {
            "status": "success",
            "filename": file.filename,
            "bucket": S3_BUCKET,
            "sha256": sha256_hash,
            "size_bytes": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
def list_files():
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        contents = response.get("Contents", [])
        files = []
        for obj in contents:
            sha256_meta = "UNVERIFIED"
            try:
                head = s3_client.head_object(Bucket=S3_BUCKET, Key=obj["Key"])
                sha256_meta = head.get("Metadata", {}).get("sha256", "UNVERIFIED")
            except Exception:
                pass
            files.append(
                {
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "sha256": sha256_meta,
                    "last_modified": obj["LastModified"].strftime("%Y-%m-%d %H:%M UTC"),
                }
            )
        return {
            "bucket": S3_BUCKET,
            "region": AWS_REGION,
            "count": len(files),
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify")
def verify_file_integrity(key: str = Query(...)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        stored_sha256 = obj.get("Metadata", {}).get("sha256")
        body_bytes = obj["Body"].read()
        computed_sha256 = hashlib.sha256(body_bytes).hexdigest()
        return {
            "key": key,
            "stored_sha256": stored_sha256,
            "computed_sha256": computed_sha256,
            "verified": bool(stored_sha256 and stored_sha256 == computed_sha256),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download")
def get_download_url(key: str = Query(...), expires: int = Query(default=3600, ge=30, le=86400)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=expires,
        )
        return {"url": url, "expires_in_seconds": expires}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete")
def delete_file(
    key: str = Query(...),
    x_vault_passcode: str | None = Header(default=None),
):
    verify_passcode(x_vault_passcode)
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        return {"status": "deleted", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
def get_lambda_cloudwatch_logs():
    try:
        start_ms = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp() * 1000)
        response = logs_client.filter_log_events(
            logGroupName=LAMBDA_LOG_GROUP,
            startTime=start_ms,
            filterPattern="CLOUDVAULT_AUDIT",
            limit=50,
        )
        raw_events = sorted(response.get("events", []), key=lambda x: x["timestamp"], reverse=True)
        parsed = []
        for ev in raw_events:
            msg = ev.get("message", "").strip()
            try:
                data = json.loads(msg)
                data["ingested_at"] = datetime.fromtimestamp(
                    ev["timestamp"] / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
                parsed.append(data)
            except Exception:
                continue
        return {"log_group": LAMBDA_LOG_GROUP, "count": len(parsed), "events": parsed}
    except logs_client.exceptions.ResourceNotFoundException:
        return {"log_group": LAMBDA_LOG_GROUP, "count": 0, "events": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))