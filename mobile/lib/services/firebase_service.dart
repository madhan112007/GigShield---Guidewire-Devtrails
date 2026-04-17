import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

class FirebaseService {
  static Future<void> initialize() async {
    try {
      await Firebase.initializeApp();
      debugPrint('[FCM] Firebase initialized successfully');
    } catch (e) {
      debugPrint('[FCM] Firebase init failed: $e');
    }
    try {
      final settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      debugPrint('[FCM] Permission status: ${settings.authorizationStatus}');
    } catch (e) {
      debugPrint('[FCM] Permission request failed: $e');
    }
  }

  static Future<String?> getToken() async {
    try {
      final token = await FirebaseMessaging.instance.getToken();
      debugPrint('[FCM] Token: $token');
      return token;
    } catch (e) {
      debugPrint('[FCM] Token fetch failed: $e');
      return null;
    }
  }

  static void setupForegroundHandler() {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      debugPrint('[FCM] Foreground message: ${message.notification?.title} — ${message.notification?.body}');
    });
  }
}
