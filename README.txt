AgriDoctor AI -> APK
====================
Your zip had no model.onnx / labels.json / ort files (prepare.py makes them),
so do STEP 1 first, otherwise the app will open but cannot diagnose.

STEP 1 - fill offline_app (on your PC, in your project root with the .venv)
    copy this whole folder's offline_app/ over your project's offline_app/ (keep the new index.html)
    python offline_app/prepare.py
  This creates model.onnx, labels.json, kb.json, files.json and ort/ (needs internet once).

STEP 2 - build the APK (pick ONE)

  A) Android Studio (easiest)
     1. Install Android Studio.
     2. File > Open > choose the "android" folder. Let it sync (accept any Gradle prompt).
     3. Build > Build Bundle(s) / APK(s) > Build APK(s).
     4. APK is at android/app/build/outputs/apk/debug/app-debug.apk

  B) No install: GitHub Actions
     1. Put this whole folder in a new GitHub repo (git add . including offline_app/model.onnx).
        If model.onnx is over 100 MB, use Git LFS.
     2. Open the repo > Actions > "Build APK" > Run workflow.
     3. Download "AgriDoctor-apk" from the finished run.

STEP 3 - install
  Send app-debug.apk to the phone (WhatsApp/Drive/USB), tap it, allow
  "Install unknown apps", install, open "AgriDoctor AI". Fully offline.

What changed vs your web version
  - index.html: when running inside the APK it shows "Offline ready" and skips the service worker
  - Android wrapper serves files over https://appassets.androidplatform.net so WebAssembly,
    localStorage and the camera button work
  - "Take photo" opens the camera; "Choose" opens the gallery
