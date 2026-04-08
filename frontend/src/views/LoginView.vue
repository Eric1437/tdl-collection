<script setup lang="ts">
import { ref } from "vue";
import { getToken, setToken } from "../api";

const token = ref(getToken());
const mode = ref<"qr" | "code" | "desktop">("qr");
const log = ref("");
const connected = ref(false);
let ws: WebSocket | null = null;

function saveToken() {
  setToken(token.value.trim());
}

function connect() {
  saveToken();
  log.value = "";
  const t = getToken();
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const qs = new URLSearchParams({ mode: mode.value });
  if (t) {
    qs.set("token", t);
  }
  const url = `${proto}//${location.host}/ws/tdl-login?${qs.toString()}`;
  ws = new WebSocket(url);
  connected.value = true;
  ws.onmessage = (ev) => {
    log.value += typeof ev.data === "string" ? ev.data : "";
  };
  ws.onerror = () => {
    log.value += "\n[websocket error]\n";
  };
  ws.onclose = () => {
    connected.value = false;
  };
}

function disconnect() {
  ws?.close();
  ws = null;
  connected.value = false;
}

function sendLine() {
  const line = prompt("Send to tdl stdin (e.g. phone code):");
  if (line != null && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(line);
  }
}
</script>

<template>
  <div>
    <h1>Telegram login</h1>
    <p class="muted">
      Runs <code>tdl login</code> in the container. Choose QR or code flow. For desktop data import, use desktop mode
      (official Telegram Desktop install path must be visible to the server — typically not available inside Docker; prefer
      QR/code).
    </p>

    <div class="panel">
      <label>API token (stored in browser)</label>
      <input v-model="token" type="password" autocomplete="off" placeholder="Bearer token from .env" />

      <label>Mode</label>
      <select v-model="mode">
        <option value="qr">QR</option>
        <option value="code">Phone code</option>
        <option value="desktop">Desktop session import</option>
      </select>

      <div class="row">
        <button type="button" @click="connect" :disabled="connected">Connect</button>
        <button type="button" class="secondary" @click="disconnect" :disabled="!connected">Disconnect</button>
        <button type="button" class="secondary" @click="sendLine" :disabled="!connected">Send line to stdin</button>
      </div>

      <pre class="log">{{ log }}</pre>
    </div>
  </div>
</template>
