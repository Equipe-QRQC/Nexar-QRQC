import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    await ApiService().init();
    if (!mounted) return;
    if (ApiService().isAuthenticated) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF0A1628),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'QRQC',
              style: TextStyle(
                color: Color(0xFF0EA5E9),
                fontSize: 40,
                fontWeight: FontWeight.w800,
                letterSpacing: 4,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Nexa IA Mobile',
              style: TextStyle(color: Colors.white54, fontSize: 14),
            ),
            SizedBox(height: 32),
            CircularProgressIndicator(color: Color(0xFF0EA5E9), strokeWidth: 2),
          ],
        ),
      ),
    );
  }
}
