<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <div class="layout">
    <header class="header">
      <strong class="brand">tdl web</strong>
      <nav class="nav">
        <RouterLink to="/login">Telegram login</RouterLink>
        <RouterLink to="/jobs">Jobs</RouterLink>
        <RouterLink to="/gallery">Gallery</RouterLink>
      </nav>
    </header>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style>
:root {
  --bg: #0f1419;
  --fg: #e7e9ea;
  --muted: #8b98a5;
  --accent: #1d9bf0;
  --border: #38444d;
  --panel: #16181c;
  font-family: system-ui, Segoe UI, Roboto, sans-serif;
  background: var(--bg);
  color: var(--fg);
}
body {
  margin: 0;
}
a {
  color: var(--accent);
  text-decoration: none;
}
a.router-link-active {
  font-weight: 600;
}
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
}
.brand {
  letter-spacing: 0.02em;
}
.nav {
  display: flex;
  gap: 1rem;
}
.main {
  flex: 1;
  padding: 1.25rem;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}
.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
}
label {
  display: block;
  margin-top: 0.75rem;
  color: var(--muted);
  font-size: 0.85rem;
}
input,
select,
textarea,
button {
  font: inherit;
}
input,
select,
textarea {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 0.5rem 0.6rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--fg);
}
button {
  cursor: pointer;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--accent);
  color: #fff;
  margin-top: 0.75rem;
}
button.secondary {
  background: transparent;
  color: var(--fg);
}
.row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
}
.muted {
  color: var(--muted);
  font-size: 0.9rem;
}
pre.log {
  white-space: pre-wrap;
  word-break: break-word;
  background: #000;
  padding: 0.75rem;
  border-radius: 6px;
  max-height: 320px;
  overflow: auto;
  font-size: 0.8rem;
}
</style>
