import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/sensor_screen.dart';
import 'screens/doc_scan_screen.dart';
import 'screens/ocorrencias_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const QrqcApp());
}

class QrqcApp extends StatelessWidget {
  const QrqcApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'QRQC Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF0EA5E9),
          surface: Color(0xFF0F1F35),
          onSurface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFF0A1628),
        fontFamily: 'Roboto',
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0A1628),
          elevation: 0,
          iconTheme: IconThemeData(color: Colors.white),
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        '/': (_) => const SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/home': (_) => const HomeScreen(),
        '/sensor': (_) => const SensorScreen(),
        '/doc_scan': (_) => const DocScanScreen(),
        '/ocorrencias': (_) => const OcorrenciasScreen(),
        '/settings': (_) => const SettingsScreen(),
      },
    );
  }
}
