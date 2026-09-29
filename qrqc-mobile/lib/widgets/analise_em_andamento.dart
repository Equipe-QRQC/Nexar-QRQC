import 'dart:async';
import 'package:flutter/material.dart';

/// Tela de espera da análise por IA (15 a 30 s): mostra a etapa, o tempo e quanto
/// costuma demorar, em vez de um "Analisando…" parado no botão.
class AnaliseEmAndamento extends StatefulWidget {
  /// (a partir de quantos segundos, texto da etapa), em ordem.
  final List<(int, String)> etapas;
  final int segundosEsperados;
  final Color cor;

  const AnaliseEmAndamento({
    super.key,
    required this.etapas,
    required this.segundosEsperados,
    required this.cor,
  });

  @override
  State<AnaliseEmAndamento> createState() => _AnaliseEmAndamentoState();
}

class _AnaliseEmAndamentoState extends State<AnaliseEmAndamento> {
  int _segundos = 0;
  Timer? _relogio;

  @override
  void initState() {
    super.initState();
    _relogio = Timer.periodic(
      const Duration(seconds: 1),
      (_) => setState(() => _segundos++),
    );
  }

  @override
  void dispose() {
    _relogio?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final etapa = widget.etapas
        .lastWhere((e) => _segundos >= e.$1, orElse: () => widget.etapas.first)
        .$2;
    // Barra estimada: nunca chega a 100% antes da resposta
    final progresso = (_segundos / widget.segundosEsperados).clamp(0.0, 0.95);
    final passou = _segundos > widget.segundosEsperados;

    // Material: fica por cima do Scaffold; sem ele o Flutter sublinha os textos em amarelo
    return Material(
      color: const Color(0xE60A1628),
      child: Container(
        alignment: Alignment.center,
        padding: const EdgeInsets.all(28),
        child: Container(
          padding: const EdgeInsets.fromLTRB(22, 26, 22, 22),
          decoration: BoxDecoration(
            color: const Color(0xFF0F1F35),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: widget.cor.withValues(alpha: 0.35)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 44,
                height: 44,
                child: CircularProgressIndicator(
                  color: widget.cor,
                  strokeWidth: 3,
                ),
              ),
              const SizedBox(height: 20),
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 300),
                child: Text(
                  etapa,
                  key: ValueKey(etapa),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progresso,
                  minHeight: 6,
                  backgroundColor: Colors.white12,
                  valueColor: AlwaysStoppedAnimation(widget.cor),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                passou
                    ? '$_segundos s · está demorando mais que o normal, aguarde'
                    : '$_segundos s · costuma levar uns ${widget.segundosEsperados} s',
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 4),
              const Text(
                'Mantenha o app aberto',
                style: TextStyle(color: Colors.white54, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
