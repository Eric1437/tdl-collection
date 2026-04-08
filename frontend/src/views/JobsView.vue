<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { apiUrl, authHeaders } from "../api";

type Job = {
  id: string;
  status: string;
  kind: string;
  payload: Record<string, unknown>;
  error_message?: string | null;
  created_at?: string | null;
};

const kind = ref<"export_then_dl" | "dl_from_links">("export_then_dl");
const chat = ref("");
const rangeType = ref<"time" | "id" | "last">("time");
const rangeA = ref("");
const rangeB = ref("");
const lastN = ref(100);
const filterExpr = ref("");
const extensions = ref("jpg,png,mp4");
const destSubdir = ref("");
const linksText = ref("https://t.me/telegram/193");
const takeout = ref(false);
const desc = ref(false);
const group = ref(false);
const skipSame = ref(false);

const jobs = ref<Job[]>([]);
const err = ref("");
const selectedId = ref<string | null>(null);
const logText = ref("");

const selectedJob = computed(() => jobs.value.find((j) => j.id === selectedId.value));

async function loadJobs() {
  err.value = "";
  const r = await fetch(apiUrl("/api/jobs"), { headers: authHeaders() });
  if (!r.ok) {
    err.value = await r.text();
    return;
  }
  jobs.value = await r.json();
}

async function submit() {
  err.value = "";
  let body: Record<string, unknown>;
  if (kind.value === "export_then_dl") {
    let range_args: number[] | number;
    if (rangeType.value === "last") {
      range_args = Number(lastN.value);
    } else {
      const a = Number(rangeA.value);
      const b = Number(rangeB.value);
      range_args = [a, b];
    }
    body = {
      kind: "export_then_dl",
      payload: {
        chat: chat.value.trim(),
        range_type: rangeType.value,
        range_args,
        filter_expr: filterExpr.value.trim() || null,
        extensions_include: extensions.value.trim() || null,
        dest_subdir: destSubdir.value.trim(),
        takeout: takeout.value,
        desc: desc.value,
        group: group.value,
        skip_same: skipSame.value,
      },
    };
  } else {
    const links = linksText.value
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
    body = {
      kind: "dl_from_links",
      payload: {
        links,
        extensions_include: extensions.value.trim() || null,
        dest_subdir: destSubdir.value.trim(),
        takeout: takeout.value,
        desc: desc.value,
        group: group.value,
        skip_same: skipSame.value,
      },
    };
  }
  const r = await fetch(apiUrl("/api/jobs"), {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    err.value = await r.text();
    return;
  }
  await loadJobs();
}

async function cancelJob(id: string) {
  await fetch(apiUrl(`/api/jobs/${id}/cancel`), { method: "POST", headers: authHeaders() });
  await loadJobs();
  await refreshLog();
}

async function refreshLog() {
  if (!selectedId.value) {
    logText.value = "";
    return;
  }
  const r = await fetch(apiUrl(`/api/jobs/${selectedId.value}/log?tail=800`), {
    headers: authHeaders(),
  });
  if (!r.ok) {
    logText.value = await r.text();
    return;
  }
  const data = await r.json();
  logText.value = data.content || "";
}

onMounted(loadJobs);

watch(selectedId, refreshLog);

let timer: ReturnType<typeof setInterval> | null = null;
watch(
  selectedId,
  (id) => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    if (!id) {
      return;
    }
    timer = setInterval(refreshLog, 3000);
  },
  { immediate: true }
);
</script>

<template>
  <div>
    <h1>Download jobs</h1>
    <p class="muted">Tasks run in Celery. Set <code>API_TOKEN</code> in .env and paste it in the Login page.</p>

    <div class="panel">
      <h2>Create job</h2>
      <label>Kind</label>
      <select v-model="kind">
        <option value="export_then_dl">Channel export + download</option>
        <option value="dl_from_links">Download from message links</option>
      </select>

      <template v-if="kind === 'export_then_dl'">
        <label>Chat (username, id, or t.me link)</label>
        <input v-model="chat" placeholder="@channel or https://t.me/..." />

        <label>Range</label>
        <select v-model="rangeType">
          <option value="time">Unix time range</option>
          <option value="id">Message id range</option>
          <option value="last">Last N media messages</option>
        </select>

        <template v-if="rangeType === 'last'">
          <label>Last N</label>
          <input v-model.number="lastN" type="number" min="1" />
        </template>
        <template v-else>
          <div class="row">
            <div style="flex: 1">
              <label>Start</label>
              <input v-model="rangeA" type="text" />
            </div>
            <div style="flex: 1">
              <label>End</label>
              <input v-model="rangeB" type="text" />
            </div>
          </div>
        </template>

        <label>Filter expression (optional, tdl -f)</label>
        <input v-model="filterExpr" placeholder="e.g. Views>200" />
      </template>

      <template v-else>
        <label>Message links (one per line)</label>
        <textarea v-model="linksText" rows="5" placeholder="https://t.me/..." />
      </template>

      <label>Extensions include (-i), optional</label>
      <input v-model="extensions" placeholder="jpg,png,mp4" />

      <label>Destination subfolder (under download root)</label>
      <input v-model="destSubdir" placeholder="myfolder" />

      <label class="row" style="align-items: center; margin-top: 0.5rem">
        <input type="checkbox" v-model="takeout" /> takeout
        <input type="checkbox" v-model="desc" /> desc
        <input type="checkbox" v-model="group" /> group
        <input type="checkbox" v-model="skipSame" /> skip-same
      </label>

      <button type="button" @click="submit">Enqueue job</button>
      <p v-if="err" class="muted" style="color: #f4212e">{{ err }}</p>
    </div>

    <div class="panel" style="margin-top: 1rem">
      <h2>Jobs</h2>
      <button type="button" class="secondary" @click="loadJobs">Refresh</button>
      <table style="width: 100%; border-collapse: collapse; margin-top: 0.5rem">
        <thead>
          <tr style="text-align: left; border-bottom: 1px solid var(--border)">
            <th>id</th>
            <th>status</th>
            <th>kind</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="j in jobs" :key="j.id" style="border-bottom: 1px solid var(--border)">
            <td style="font-size: 0.75rem; word-break: break-all">
              <a href="#" @click.prevent="selectedId = j.id">{{ j.id.slice(0, 8) }}…</a>
            </td>
            <td>{{ j.status }}</td>
            <td>{{ j.kind }}</td>
            <td>
              <button type="button" class="secondary" @click="cancelJob(j.id)">Cancel</button>
            </td>
          </tr>
        </tbody>
      </table>

      <template v-if="selectedJob">
        <h3 style="margin-top: 1rem">Selected</h3>
        <pre class="log" style="max-height: 160px">{{ JSON.stringify(selectedJob, null, 2) }}</pre>
        <h3>Log</h3>
        <button type="button" class="secondary" @click="refreshLog">Refresh log</button>
        <pre class="log">{{ logText }}</pre>
      </template>
    </div>
  </div>
</template>
