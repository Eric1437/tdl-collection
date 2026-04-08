<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { apiUrl, authHeaders, mediaUrl } from "../api";

type Entry = {
  name: string;
  path: string;
  is_dir: boolean;
  size: number | null;
};

const path = ref("");
const entries = ref<Entry[]>([]);
const err = ref("");
const preview = ref<Entry | null>(null);

const crumbs = computed(() => {
  if (!path.value) {
    return [];
  }
  return path.value.split("/").filter(Boolean);
});

async function load() {
  err.value = "";
  const q = new URLSearchParams();
  if (path.value) {
    q.set("path", path.value);
  }
  const url = apiUrl(`/api/files/browse?${q.toString()}`);
  const r = await fetch(url, { headers: authHeaders() });
  if (!r.ok) {
    err.value = await r.text();
    return;
  }
  entries.value = await r.json();
}

function enter(e: Entry) {
  if (e.is_dir) {
    path.value = e.path;
    preview.value = null;
    load();
  } else {
    preview.value = e;
  }
}

function up() {
  const parts = path.value.split("/").filter(Boolean);
  parts.pop();
  path.value = parts.join("/");
  preview.value = null;
  load();
}

function goRoot() {
  path.value = "";
  preview.value = null;
  load();
}

function crumbTo(i: number) {
  const parts = crumbs.value.slice(0, i + 1);
  path.value = parts.join("/");
  preview.value = null;
  load();
}

watch(path, load, { immediate: true });

const isImage = (name: string) => /\.(jpe?g|png|gif|webp|bmp|svg)$/i.test(name);
const isVideo = (name: string) => /\.(mp4|webm|mkv|mov)$/i.test(name);
</script>

<template>
  <div>
    <h1>Downloads</h1>
    <p class="muted">Browse files under the server download directory.</p>
    <div class="panel">
      <div class="row" style="align-items: center">
        <button type="button" class="secondary" @click="goRoot" :disabled="!path">Root</button>
        <button type="button" class="secondary" @click="up" :disabled="!path">Up</button>
        <span class="muted" style="margin: 0">
          <template v-for="(c, i) in crumbs" :key="i">
            / <a href="#" @click.prevent="crumbTo(i)">{{ c }}</a>
          </template>
        </span>
      </div>
      <p v-if="err" style="color: #f4212e">{{ err }}</p>
      <ul style="list-style: none; padding: 0">
        <li v-for="e in entries" :key="e.path" style="padding: 0.35rem 0; border-bottom: 1px solid var(--border)">
          <a href="#" @click.prevent="enter(e)">
            {{ e.is_dir ? "[dir]" : "[file]" }} {{ e.name }}
            <span v-if="!e.is_dir && e.size != null" class="muted">({{ e.size }} bytes)</span>
          </a>
        </li>
      </ul>
    </div>

    <div v-if="preview && !preview.is_dir" class="panel" style="margin-top: 1rem">
      <h3>{{ preview.name }}</h3>
      <img
        v-if="isImage(preview.name)"
        :src="mediaUrl(preview.path)"
        alt=""
        style="max-width: 100%; border-radius: 8px"
      />
      <video
        v-else-if="isVideo(preview.name)"
        :src="mediaUrl(preview.path)"
        controls
        style="max-width: 100%; border-radius: 8px"
      />
      <p v-else class="muted">No inline preview. Open: <code>{{ mediaUrl(preview.path) }}</code></p>
    </div>
  </div>
</template>
