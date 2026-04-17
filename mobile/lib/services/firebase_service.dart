import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

class FirebaseService {
  static Future<void> initialize() async {
    await Firebase.initializeApp();
    await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
  }

  static Future<String?> getToken() async {
    try {
      return await FirebaseMessaging.instance.getToken();
    } catch (e) {
      print('[FCM] Token fetch failed: $e');
      return null;
    }
  }

  static void setupForegroundHandler() {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('[FCM] Foreground message: ${message.notification?.title}');
    });
  }
}
