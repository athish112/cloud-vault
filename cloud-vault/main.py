import os
import boto3
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CloudVault — Enterprise Cloud Storage Console")

S3_BUCKET = os.getenv("S3_BUCKET_NAME", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=AWS_REGION,
)


@app.get("/", response_class=HTMLResponse)
def home():
    return r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>CloudVault | AWS S3 Containerized Storage Console</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-base: #070b14;
                --bg-surface: rgba(15, 23, 42, 0.72);
                --bg-card: rgba(17, 25, 45, 0.85);
                --bg-hover: rgba(30, 41, 59, 0.75);
                --border: rgba(148, 163, 184, 0.14);
                --border-glow: rgba(99, 102, 241, 0.45);
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --text-muted: #64748b;
                --accent: #6366f1;
                --accent-cyan: #06b6d4;
                --success: #10b981;
                --danger: #ef4444;
                --warning: #f59e0b;
            }

            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background-color: var(--bg-base);
                color: var(--text-primary);
                min-height: 100vh;
                overflow-x: hidden;
                background-image:
                    radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.16), transparent 38%),
                    radial-gradient(circle at 85% 15%, rgba(6, 182, 212, 0.13), transparent 36%),
                    linear-gradient(rgba(148, 163, 184, 0.04) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(148, 163, 184, 0.04) 1px, transparent 1px);
                background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px;
            }

            /* Top Navigation Bar */
            .navbar {
                position: sticky;
                top: 0;
                z-index: 50;
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                background: rgba(7, 11, 20, 0.78);
                border-bottom: 1px solid var(--border);
            }

            .nav-inner {
                max-width: 1180px;
                margin: 0 auto;
                padding: 14px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                flex-wrap: wrap;
            }

            .brand {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .brand-icon {
                width: 38px;
                height: 38px;
                border-radius: 10px;
                background: linear-gradient(135deg, var(--accent), var(--accent-cyan));
                display: grid;
                place-items: center;
                box-shadow: 0 0 24px rgba(99, 102, 241, 0.4);
            }

            .brand-title {
                font-size: 1.15rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            .brand-sub {
                font-size: 0.75rem;
                color: var(--text-secondary);
                font-family: 'JetBrains Mono', monospace;
            }

            .nav-pills {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            .status-pill {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 12px;
                border-radius: 999px;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.28);
                color: #6ee7b7;
                font-size: 0.78rem;
                font-family: 'JetBrains Mono', monospace;
            }

            .pulse-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--success);
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
                100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }

            .nav-link {
                color: var(--text-secondary);
                text-decoration: none;
                font-size: 0.82rem;
                font-weight: 500;
                padding: 7px 12px;
                border-radius: 8px;
                border: 1px solid var(--border);
                background: rgba(15, 23, 42, 0.5);
                transition: all 0.2s ease;
            }

            .nav-link:hover {
                color: var(--text-primary);
                border-color: var(--border-glow);
                background: var(--bg-hover);
            }

            /* Main Container */
            .container {
                max-width: 1180px;
                margin: 0 auto;
                padding: 28px 24px 60px;
            }

            /* View Switcher Tabs */
            .view-tabs {
                display: inline-flex;
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 4px;
                margin-bottom: 24px;
            }

            .tab-btn {
                border: none;
                background: transparent;
                color: var(--text-secondary);
                padding: 9px 18px;
                border-radius: 9px;
                font-size: 0.86rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .tab-btn.active {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(6, 182, 212, 0.2));
                color: var(--text-primary);
                border: 1px solid rgba(99, 102, 241, 0.35);
            }

            /* KPI Grid */
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }

            .kpi-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 18px 20px;
                backdrop-filter: blur(12px);
                transition: transform 0.2s ease, border-color 0.2s ease;
            }

            .kpi-card:hover {
                transform: translateY(-2px);
                border-color: var(--border-glow);
            }

            .kpi-label {
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: var(--text-secondary);
                margin-bottom: 8px;
            }

            .kpi-value {
                font-size: 1.45rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                color: var(--text-primary);
            }

            .kpi-meta {
                margin-top: 6px;
                font-size: 0.76rem;
                font-family: 'JetBrains Mono', monospace;
                color: var(--accent-cyan);
            }

            /* Dashboard Two-Column Layout */
            .dashboard-grid {
                display: grid;
                grid-template-columns: 390px 1fr;
                gap: 22px;
                align-items: start;
            }

            @media (max-width: 920px) {
                .dashboard-grid {
                    grid-template-columns: 1fr;
                }
            }

            .panel {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 22px;
                backdrop-filter: blur(14px);
                box-shadow: 0 20px 45px -20px rgba(0, 0, 0, 0.65);
            }

            .panel-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
                gap: 12px;
            }

            .panel-title {
                font-size: 1rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* Dropzone */
            .dropzone {
                border: 2px dashed rgba(99, 102, 241, 0.38);
                border-radius: 14px;
                padding: 32px 20px;
                text-align: center;
                background: rgba(99, 102, 241, 0.04);
                cursor: pointer;
                transition: all 0.22s ease;
            }

            .dropzone:hover, .dropzone.dragover {
                border-color: var(--accent-cyan);
                background: rgba(6, 182, 212, 0.08);
                transform: scale(1.01);
            }

            .drop-icon {
                width: 48px;
                height: 48px;
                margin: 0 auto 12px;
                border-radius: 12px;
                background: rgba(99, 102, 241, 0.15);
                color: #a5b4fc;
                display: grid;
                place-items: center;
            }

            .drop-title {
                font-size: 0.94rem;
                font-weight: 600;
                margin-bottom: 4px;
            }

            .drop-hint {
                font-size: 0.8rem;
                color: var(--text-secondary);
            }

            /* Selected File Preview */
            .file-preview {
                display: none;
                margin-top: 14px;
                padding: 12px 14px;
                border-radius: 10px;
                background: rgba(15, 23, 42, 0.9);
                border: 1px solid var(--border-glow);
                align-items: center;
                justify-content: space-between;
                gap: 10px;
            }

            .file-preview.visible {
                display: flex;
            }

            .file-preview-info {
                overflow: hidden;
            }

            .file-preview-name {
                font-size: 0.85rem;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .file-preview-size {
                font-size: 0.74rem;
                color: var(--text-secondary);
                font-family: 'JetBrains Mono', monospace;
            }

            .clear-btn {
                background: transparent;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                font-size: 0.82rem;
                padding: 4px 8px;
                border-radius: 6px;
            }

            .clear-btn:hover {
                color: var(--danger);
                background: rgba(239, 68, 68, 0.12);
            }

            /* Progress Bar */
            .progress-wrap {
                display: none;
                margin-top: 14px;
            }

            .progress-wrap.visible {
                display: block;
            }

            .progress-bar-bg {
                width: 100%;
                height: 7px;
                border-radius: 999px;
                background: rgba(148, 163, 184, 0.16);
                overflow: hidden;
            }

            .progress-bar-fill {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, var(--accent), var(--accent-cyan));
                transition: width 0.2s ease;
            }

            .progress-label {
                margin-top: 6px;
                font-size: 0.75rem;
                color: var(--text-secondary);
                font-family: 'JetBrains Mono', monospace;
                text-align: right;
            }

            /* Primary Button */
            .btn-primary {
                width: 100%;
                margin-top: 16px;
                padding: 12px 18px;
                border: none;
                border-radius: 10px;
                font-size: 0.9rem;
                font-weight: 600;
                color: #ffffff;
                background: linear-gradient(135deg, var(--accent), #4f46e5);
                box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.65);
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                transition: all 0.2s ease;
            }

            .btn-primary:hover:not(:disabled) {
                transform: translateY(-1px);
                box-shadow: 0 12px 24px -6px rgba(99, 102, 241, 0.85);
            }

            .btn-primary:disabled {
                opacity: 0.55;
                cursor: not-allowed;
            }

            /* Search & Refresh Controls */
            .toolbar {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }

            .search-input {
                background: rgba(7, 11, 20, 0.75);
                border: 1px solid var(--border);
                border-radius: 9px;
                padding: 8px 12px;
                color: var(--text-primary);
                font-size: 0.84rem;
                min-width: 200px;
                outline: none;
                transition: border-color 0.2s ease;
            }

            .search-input:focus {
                border-color: var(--accent);
            }

            .btn-icon {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid var(--border);
                color: var(--text-secondary);
                border-radius: 9px;
                padding: 8px 12px;
                font-size: 0.82rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .btn-icon:hover {
                color: var(--text-primary);
                border-color: var(--border-glow);
            }

            /* File Table */
            .table-wrap {
                overflow-x: auto;
                border-radius: 12px;
                border: 1px solid var(--border);
            }

            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }

            th {
                background: rgba(7, 11, 20, 0.7);
                padding: 12px 14px;
                font-size: 0.74rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-secondary);
                border-bottom: 1px solid var(--border);
            }

            td {
                padding: 13px 14px;
                font-size: 0.86rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.08);
                vertical-align: middle;
            }

            tr:last-child td {
                border-bottom: none;
            }

            tbody tr {
                transition: background 0.15s ease;
            }

            tbody tr:hover {
                background: rgba(30, 41, 59, 0.45);
            }

            .ext-badge {
                display: inline-block;
                padding: 3px 7px;
                border-radius: 6px;
                font-size: 0.7rem;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
                background: rgba(99, 102, 241, 0.18);
                color: #a5b4fc;
                margin-right: 8px;
                text-transform: uppercase;
            }

            .mono {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
                color: var(--text-secondary);
            }

            .action-group {
                display: inline-flex;
                gap: 6px;
            }

            .btn-sm {
                padding: 5px 10px;
                border-radius: 7px;
                font-size: 0.78rem;
                font-weight: 500;
                border: 1px solid var(--border);
                background: rgba(15, 23, 42, 0.9);
                color: var(--text-primary);
                cursor: pointer;
                transition: all 0.15s ease;
            }

            .btn-sm:hover {
                border-color: var(--accent-cyan);
                color: var(--accent-cyan);
            }

            .btn-sm.danger:hover {
                border-color: var(--danger);
                color: #fca5a5;
                background: rgba(239, 68, 68, 0.12);
            }

            .empty-state {
                padding: 40px 20px;
                text-align: center;
                color: var(--text-secondary);
                font-size: 0.88rem;
            }

            /* Architecture View */
            .arch-section {
                display: none;
            }

            .arch-section.active {
                display: block;
            }

            .flow-diagram {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
                gap: 14px;
                margin-bottom: 22px;
            }

            .flow-node {
                background: rgba(7, 11, 20, 0.75);
                border: 1px solid var(--border-glow);
                border-radius: 12px;
                padding: 16px;
            }

            .flow-tag {
                font-size: 0.7rem;
                font-family: 'JetBrains Mono', monospace;
                color: var(--accent-cyan);
                margin-bottom: 6px;
            }

            .flow-title {
                font-size: 0.95rem;
                font-weight: 700;
                margin-bottom: 6px;
            }

            .flow-desc {
                font-size: 0.8rem;
                color: var(--text-secondary);
                line-height: 1.45;
            }

            .module-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 14px;
            }

            .module-card {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 16px;
            }

            .module-card h4 {
                font-size: 0.88rem;
                color: #a5b4fc;
                margin-bottom: 6px;
            }

            .module-card p {
                font-size: 0.82rem;
                color: var(--text-secondary);
                line-height: 1.5;
            }

            /* Toast Notification */
            .toast {
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 100;
                padding: 13px 18px;
                border-radius: 12px;
                background: rgba(15, 23, 42, 0.96);
                border: 1px solid var(--border-glow);
                color: var(--text-primary);
                font-size: 0.85rem;
                box-shadow: 0 18px 36px rgba(0, 0, 0, 0.65);
                transform: translateY(120%);
                opacity: 0;
                transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
            }

            .toast.show {
                transform: translateY(0);
                opacity: 1;
            }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="nav-inner">
                <div class="brand">
                    <div class="brand-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="brand-title">CloudVault Console</div>
                        <div class="brand-sub">FastAPI • Docker • AWS EC2 + S3</div>
                    </div>
                </div>

                <div class="nav-pills">
                    <div class="status-pill" id="connectionBadge">
                        <span class="pulse-dot"></span>
                        <span id="statusText">Connecting to AWS S3...</span>
                    </div>
                    <a class="nav-link" href="/files" target="_blank">Raw JSON</a>
                    <a class="nav-link" href="/docs" target="_blank">Swagger API</a>
                </div>
            </div>
        </nav>

        <main class="container">
            <div class="view-tabs">
                <button class="tab-btn active" id="tabConsole" onclick="switchTab('console')">Storage Console</button>
                <button class="tab-btn" id="tabArch" onclick="switchTab('arch')">Cloud Architecture & 5-Module Map</button>
            </div>

            <!-- TAB 1: LIVE STORAGE CONSOLE -->
            <section id="viewConsole">
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">S3 Objects Stored</div>
                        <div class="kpi-value" id="kpiCount">—</div>
                        <div class="kpi-meta" id="kpiBucket">Bucket: loading...</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Total Cloud Storage</div>
                        <div class="kpi-value" id="kpiSize">—</div>
                        <div class="kpi-meta">Class: S3 Standard (99.999999999%)</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Compute & Runtime</div>
                        <div class="kpi-value">Docker on EC2</div>
                        <div class="kpi-meta">Amazon Linux 2023 • Port 8000</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Deployment Pipeline</div>
                        <div class="kpi-value">GitHub Actions</div>
                        <div class="kpi-meta">Automated CI/CD Container Build</div>
                    </div>
                </div>

                <div class="dashboard-grid">
                    <!-- Upload Card -->
                    <div class="panel">
                        <div class="panel-header">
                            <div class="panel-title">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#818cf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                                </svg>
                                Upload Object to S3
                            </div>
                        </div>

                        <div class="dropzone" id="dropzone">
                            <div class="drop-icon">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>
                                </svg>
                            </div>
                            <div class="drop-title">Drag & drop a file here, or click to browse</div>
                            <div class="drop-hint">Streamed via FastAPI & boto3 directly to Amazon S3</div>
                            <input type="file" id="fileInput" hidden />
                        </div>

                        <div class="file-preview" id="filePreview">
                            <div class="file-preview-info">
                                <div class="file-preview-name" id="previewName"></div>
                                <div class="file-preview-size" id="previewSize"></div>
                            </div>
                            <button type="button" class="clear-btn" onclick="clearFile()">Remove</button>
                        </div>

                        <div class="progress-wrap" id="progressWrap">
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" id="progressFill"></div>
                            </div>
                            <div class="progress-label" id="progressLabel">Uploading... 0%</div>
                        </div>

                        <button type="button" class="btn-primary" id="uploadBtn" onclick="uploadSelectedFile()" disabled>
                            Deploy File to AWS S3
                        </button>
                    </div>

                    <!-- S3 Object Explorer -->
                    <div class="panel">
                        <div class="panel-header">
                            <div class="panel-title">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>
                                </svg>
                                Live S3 Bucket Explorer
                            </div>
                            <div class="toolbar">
                                <input type="text" class="search-input" id="searchInput" placeholder="Filter objects by name..." oninput="renderFiles()" />
                                <button type="button" class="btn-icon" onclick="loadFiles()">↻ Refresh</button>
                            </div>
                        </div>

                        <div class="table-wrap">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Object Key</th>
                                        <th>Size</th>
                                        <th>Last Modified</th>
                                        <th style="text-align: right;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="filesTableBody">
                                    <tr>
                                        <td colspan="4" class="empty-state">Fetching objects from Amazon S3...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </section>

            <!-- TAB 2: ARCHITECTURE & SYLLABUS MAP -->
            <section id="viewArch" class="arch-section">
                <div class="panel" style="margin-bottom: 20px;">
                    <div class="panel-header">
                        <div class="panel-title">End-to-End Cloud Deployment Topology</div>
                    </div>
                    <div class="flow-diagram">
                        <div class="flow-node">
                            <div class="flow-tag">1. VERSION CONTROL & CI/CD</div>
                            <div class="flow-title">GitHub + Actions</div>
                            <div class="flow-desc">Every push to <code>main</code> triggers an Ubuntu runner to build and verify the Docker image automatically.</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">2. CONTAINER RUNTIME</div>
                            <div class="flow-title">Docker Engine</div>
                            <div class="flow-desc">Packages Python 3.11-slim, FastAPI, and boto3 into a portable, isolated microservice container.</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">3. CLOUD COMPUTE (IaaS)</div>
                            <div class="flow-title">Amazon EC2</div>
                            <div class="flow-desc">Hosted on Amazon Linux 2023 in <code>ap-south-1</code> with Security Group ingress on ports 22 & 8000.</div>
                        </div>
                        <div class="flow-node">
                            <div class="flow-tag">4. OBJECT STORAGE</div>
                            <div class="flow-title">Amazon S3</div>
                            <div class="flow-desc">Stateless file persistence via IAM-authenticated <code>boto3</code> SDK calls independent of container lifecycle.</div>
                        </div>
                    </div>

                    <div class="module-grid">
                        <div class="module-card">
                            <h4>Module 1 — Cloud & Virtualization (CO1)</h4>
                            <p>Demonstrates transition from heavy hypervisor-based local virtual machines to lightweight OS-level Docker containers sharing the host Linux kernel.</p>
                        </div>
                        <div class="module-card">
                            <h4>Module 2 — Cloud Architectures & Models (CO2)</h4>
                            <p>Combines <strong>IaaS</strong> (Amazon EC2), <strong>SaaS</strong> (GitHub & Actions), and Public Cloud multi-tenant object storage in AWS Mumbai (<code>ap-south-1</code>).</p>
                        </div>
                        <div class="module-card">
                            <h4>Module 3 — 7-Step Cloud Migration (CO3)</h4>
                            <p>Migrated from local storage (<code>127.0.0.1</code>) to stateless AWS infrastructure by externalizing <code>.env</code> secrets and decoupling file persistence to S3.</p>
                        </div>
                        <div class="module-card">
                            <h4>Module 4 — Cloud Programming on AWS (CO4)</h4>
                            <p>Implements programmatic cloud storage operations (<code>upload_fileobj</code>, <code>list_objects_v2</code>, <code>generate_presigned_url</code>) using AWS SDK for Python.</p>
                        </div>
                        <div class="module-card">
                            <h4>Module 5 — Git, Docker & CI/CD (CO5)</h4>
                            <p>Uses Git branching/commits, multi-layer <code>Dockerfile</code> packaging, and automated YAML build pipelines in <code>.github/workflows/docker-ci.yml</code>.</p>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <div class="toast" id="toast"></div>

        <script>
            let allFiles = [];
            let selectedFile = null;

            function switchTab(tab) {
                const isConsole = tab === 'console';
                document.getElementById('viewConsole').style.display = isConsole ? 'block' : 'none';
                document.getElementById('viewArch').classList.toggle('active', !isConsole);
                document.getElementById('tabConsole').classList.toggle('active', isConsole);
                document.getElementById('tabArch').classList.toggle('active', !isConsole);
            }

            function showToast(message, isError = false) {
                const toast = document.getElementById('toast');
                toast.textContent = message;
                toast.style.borderColor = isError ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)';
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 3400);
            }

            function formatBytes(bytes) {
                if (!bytes || bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }

            function escapeHtml(str) {
                return str.replace(/[&<>"']/g, m => ({
                    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
                }[m]));
            }

            function getExt(filename) {
                const parts = filename.split('.');
                return parts.length > 1 ? parts.pop().slice(0, 4) : 'FILE';
            }

            // Drag and Drop Handling
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');

            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('dragover');
            });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    setFile(e.dataTransfer.files[0]);
                }
            });
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length) {
                    setFile(fileInput.files[0]);
                }
            });

            function setFile(file) {
                selectedFile = file;
                document.getElementById('previewName').textContent = file.name;
                document.getElementById('previewSize').textContent = formatBytes(file.size);
                document.getElementById('filePreview').classList.add('visible');
                document.getElementById('uploadBtn').disabled = false;
            }

            function clearFile() {
                selectedFile = null;
                fileInput.value = '';
                document.getElementById('filePreview').classList.remove('visible');
                document.getElementById('uploadBtn').disabled = true;
            }

            function uploadSelectedFile() {
                if (!selectedFile) return;

                const btn = document.getElementById('uploadBtn');
                const progressWrap = document.getElementById('progressWrap');
                const progressFill = document.getElementById('progressFill');
                const progressLabel = document.getElementById('progressLabel');

                btn.disabled = true;
                progressWrap.classList.add('visible');
                progressFill.style.width = '15%';
                progressLabel.textContent = 'Streaming to AWS S3...';

                const formData = new FormData();
                formData.append('file', selectedFile);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload', true);

                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const pct = Math.min(95, Math.round((e.loaded / e.total) * 100));
                        progressFill.style.width = pct + '%';
                        progressLabel.textContent = `Uploading... ${pct}%`;
                    }
                };

                xhr.onload = () => {
                    progressFill.style.width = '100%';
                    if (xhr.status >= 200 && xhr.status < 300) {
                        const res = JSON.parse(xhr.responseText);
                        showToast(`Uploaded "${res.filename}" to ${res.bucket}`);
                        clearFile();
                        loadFiles();
                    } else {
                        let msg = 'Upload failed';
                        try { msg = JSON.parse(xhr.responseText).detail || msg; } catch (_) {}
                        showToast(msg, true);
                        btn.disabled = false;
                    }
                    setTimeout(() => {
                        progressWrap.classList.remove('visible');
                        progressFill.style.width = '0%';
                    }, 600);
                };

                xhr.onerror = () => {
                    showToast('Network error while uploading to S3', true);
                    btn.disabled = false;
                    progressWrap.classList.remove('visible');
                };

                xhr.send(formData);
            }

            async function loadFiles() {
                try {
                    const res = await fetch('/files');
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Failed to load S3 bucket');

                    allFiles = data.files || [];
                    document.getElementById('statusText').textContent = `Connected • ${data.region}`;
                    document.getElementById('kpiCount').textContent = data.count;
                    document.getElementById('kpiBucket').textContent = `Bucket: ${data.bucket}`;
                    document.getElementById('kpiSize').textContent = formatBytes(data.total_size_bytes);
                    renderFiles();
                } catch (err) {
                    document.getElementById('statusText').textContent = 'S3 Connection Error';
                    document.getElementById('filesTableBody').innerHTML =
                        `<tr><td colspan="4" class="empty-state" style="color:#fca5a5;">${escapeHtml(err.message)}</td></tr>`;
                }
            }

            function renderFiles() {
                const query = document.getElementById('searchInput').value.toLowerCase();
                const tbody = document.getElementById('filesTableBody');
                const filtered = allFiles.filter(f => f.key.toLowerCase().includes(query));

                if (!filtered.length) {
                    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No objects found in S3 bucket. Upload a file to begin.</td></tr>`;
                    return;
                }

                tbody.innerHTML = filtered.map(f => `
                    <tr>
                        <td>
                            <span class="ext-badge">${escapeHtml(getExt(f.key))}</span>
                            <strong>${escapeHtml(f.key)}</strong>
                        </td>
                        <td class="mono">${formatBytes(f.size)}</td>
                        <td class="mono">${escapeHtml(f.last_modified)}</td>
                        <td style="text-align: right;">
                            <div class="action-group">
                                <button class="btn-sm" onclick="downloadFile(${JSON.stringify(f.key)})">Open</button>
                                <button class="btn-sm danger" onclick="deleteFile(${JSON.stringify(f.key)})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }

            async function downloadFile(key) {
                try {
                    const res = await fetch(`/download?key=${encodeURIComponent(key)}`);
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Unable to generate S3 link');
                    window.open(data.url, '_blank');
                } catch (err) {
                    showToast(err.message, true);
                }
            }

            async function deleteFile(key) {
                if (!confirm(`Delete "${key}" from Amazon S3?`)) return;
                try {
                    const res = await fetch(`/delete?key=${encodeURIComponent(key)}`, { method: 'DELETE' });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.detail || 'Delete failed');
                    showToast(`Deleted "${key}" from S3`);
                    loadFiles();
                } catch (err) {
                    showToast(err.message, true);
                }
            }

            loadFiles();
        </script>
    </body>
    </html>
    """


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET, file.filename)
        return {"status": "success", "filename": file.filename, "bucket": S3_BUCKET}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files")
def list_files():
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        contents = response.get("Contents", [])
        files = [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].strftime("%Y-%m-%d %H:%M UTC"),
            }
            for obj in contents
        ]
        total_size = sum(obj["Size"] for obj in contents)
        return {
            "bucket": S3_BUCKET,
            "region": AWS_REGION,
            "count": len(files),
            "total_size_bytes": total_size,
            "files": files,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download")
def get_download_url(key: str = Query(...)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=3600,
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete")
def delete_file(key: str = Query(...)):
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET_NAME is not configured.")
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        return {"status": "deleted", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))