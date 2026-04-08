import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import JobsView from "../views/JobsView.vue";
import GalleryView from "../views/GalleryView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", redirect: "/jobs" },
    { path: "/login", name: "login", component: LoginView },
    { path: "/jobs", name: "jobs", component: JobsView },
    { path: "/gallery", name: "gallery", component: GalleryView },
  ],
});

export default router;
