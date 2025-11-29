import * as admin from "firebase-admin";
import serviceAccount from "./serviceAccountKey.json";

let app: admin.app.App;

if (!admin.apps.length) {
  app = admin.initializeApp({
    credential: admin.credential.cert(serviceAccount as admin.ServiceAccount),
  });
} else {
  app = admin.app();
}

export const firebaseAdmin = app;
export const fcm = app.messaging();