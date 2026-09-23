import 'package:flutter/material.dart';

class SeverityChip extends StatelessWidget {
  final String severity;
  final bool small;

  const SeverityChip(this.severity, {super.key, this.small = false});

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (severity) {
      'critico' || 'alto' => ('Crítico', const Color(0xFFEF4444)),
      'atencao' || 'medio' => ('Atenção', const Color(0xFFF59E0B)),
      _ => ('Info', const Color(0xFF3B82F6)),
    };
    final fs = small ? 10.0 : 11.0;
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: small ? 6 : 8,
        vertical: small ? 2 : 3,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        border: Border.all(color: color.withOpacity(0.6)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: fs,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}

class HealthGauge extends StatelessWidget {
  final int? score;

  const HealthGauge(this.score, {super.key});

  @override
  Widget build(BuildContext context) {
    if (score == null) return const SizedBox.shrink();
    final s = score!;
    final color = s >= 80
        ? const Color(0xFF22C55E)
        : s >= 55
            ? const Color(0xFFF59E0B)
            : const Color(0xFFEF4444);
    return Column(
      children: [
        Text(
          '$s',
          style: TextStyle(
            color: color,
            fontSize: 48,
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          'Índice de Saúde / 100',
          style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 12),
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: s / 100,
            backgroundColor: Colors.white12,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 8,
          ),
        ),
      ],
    );
  }
}
