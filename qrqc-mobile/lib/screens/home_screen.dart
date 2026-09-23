import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A1628),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        elevation: 0,
        title: const Row(
          children: [
            Text(
              'QRQC',
              style: TextStyle(
                color: Color(0xFF0EA5E9),
                fontWeight: FontWeight.w800,
                letterSpacing: 2,
              ),
            ),
            SizedBox(width: 8),
            Text(
              'Mobile',
              style: TextStyle(color: Colors.white54, fontSize: 14),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white54, size: 20),
            onPressed: () async {
              await ApiService().logout();
              if (!context.mounted) return;
              Navigator.pushReplacementNamed(context, '/login');
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'O que deseja inspecionar?',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Selecione uma função abaixo',
                style: TextStyle(color: Colors.white38, fontSize: 13),
              ),
              const SizedBox(height: 24),
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 14,
                  mainAxisSpacing: 14,
                  childAspectRatio: 0.9,
                  children: [
                    _MenuCard(
                      icon: Icons.camera_alt_outlined,
                      title: 'Sensor Visual',
                      subtitle: 'Detecta anomalias em equipamentos',
                      color: const Color(0xFF0EA5E9),
                      onTap: () => Navigator.pushNamed(context, '/sensor'),
                    ),
                    _MenuCard(
                      icon: Icons.document_scanner_outlined,
                      title: 'Inspecionar Documento',
                      subtitle: 'Encontra erros em formulários e laudos',
                      color: const Color(0xFF8B5CF6),
                      onTap: () =>
                          Navigator.pushNamed(context, '/doc_scan'),
                    ),
                    _MenuCard(
                      icon: Icons.warning_amber_outlined,
                      title: 'Ocorrências',
                      subtitle: 'Visualizar e registrar ocorrências',
                      color: const Color(0xFFF59E0B),
                      onTap: () =>
                          Navigator.pushNamed(context, '/ocorrencias'),
                    ),
                    _MenuCard(
                      icon: Icons.settings_outlined,
                      title: 'Configurações',
                      subtitle: 'Servidor e preferências',
                      color: const Color(0xFF6B7280),
                      onTap: () =>
                          Navigator.pushNamed(context, '/settings'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MenuCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _MenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0xFF0F1F35),
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const Spacer(),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style:
                    const TextStyle(color: Colors.white38, fontSize: 11),
                maxLines: 2,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
