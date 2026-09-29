import 'dart:io';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/severity_chip.dart';
import 'nova_ocorrencia_screen.dart';

Color corDaSeveridade(String s) => switch (s) {
      'critico' => const Color(0xFFEF4444),
      'atencao' => const Color(0xFFF59E0B),
      _ => const Color(0xFF3B82F6),
    };

class ResultSensorScreen extends StatefulWidget {
  final ResultadoSensor resultado;
  final File foto;

  const ResultSensorScreen({super.key, required this.resultado, required this.foto});

  @override
  State<ResultSensorScreen> createState() => _ResultSensorScreenState();
}

class _ResultSensorScreenState extends State<ResultSensorScreen> {
  int? _selecionada;
  late final List<GlobalKey> _chaves =
      List.generate(widget.resultado.anomalias.length, (_) => GlobalKey());
  bool _validando = false;
  bool _validado = false;
  bool _baixandoPdf = false;

  ResultadoSensor get r => widget.resultado;

  void _selecionar(int i, {bool rolar = false}) {
    setState(() => _selecionada = _selecionada == i ? null : i);
    if (rolar && _selecionada != null) {
      // Caixa tocada na foto → leva até o card dela
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final ctx = _chaves[i].currentContext;
        if (ctx != null) {
          Scrollable.ensureVisible(ctx, duration: const Duration(milliseconds: 300), alignment: 0.1);
        }
      });
    }
  }

  Future<void> _abrirOcorrencia() async {
    final id = await Navigator.push<int>(
      context,
      MaterialPageRoute(
        builder: (_) => NovaOcorrenciaScreen(
          maquinaId: r.maquinaId,
          componenteId: r.componenteId,
          texto: r.textoParaOcorrencia(),
          risco: r.severidadeMax == 'critico',
          inspecaoId: r.id,
        ),
      ),
    );
    if (id != null) _avisar('Ocorrência nº $id registrada a partir desta inspeção.', erro: false);
  }

  Future<void> _validar() async {
    setState(() => _validando = true);
    try {
      await ApiService().validarInspecao(r.id!);
      if (mounted) setState(() => _validado = true);
    } catch (e) {
      _avisar(e.toString());
    } finally {
      if (mounted) setState(() => _validando = false);
    }
  }

  Future<void> _compartilharLaudo(BuildContext botao) async {
    // Posição do botão: o iPad exige para ancorar a folha de compartilhamento
    final caixa = botao.findRenderObject() as RenderBox?;
    final origem = caixa == null ? null : caixa.localToGlobal(Offset.zero) & caixa.size;
    setState(() => _baixandoPdf = true);
    try {
      final pdf = await ApiService().baixarLaudo(r.id!);
      await SharePlus.instance.share(ShareParams(
        files: [XFile.fromData(pdf, mimeType: 'application/pdf')],
        fileNameOverrides: ['laudo_inspecao_${r.id}.pdf'],
        subject: 'Laudo de inspeção visual nº ${r.id}',
        sharePositionOrigin: origem,
      ));
    } catch (e) {
      _avisar(e.toString());
    } finally {
      if (mounted) setState(() => _baixandoPdf = false);
    }
  }

  void _avisar(String msg, {bool erro = true}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: erro ? const Color(0xFFEF4444) : const Color(0xFF22C55E),
      behavior: SnackBarBehavior.floating,
    ));
  }

  @override
  Widget build(BuildContext context) {
    final anomalias = r.anomalias;
    return Scaffold(
      backgroundColor: const Color(0xFF0A1628),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 18),
          tooltip: 'Voltar',
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(r.id != null ? 'Inspeção nº ${r.id}' : 'Resultado da inspeção'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _FotoComAnomalias(
                foto: widget.foto,
                anomalias: anomalias,
                selecionada: _selecionada,
                onTocar: (i) => _selecionar(i, rolar: true),
              ),
              if (anomalias.isNotEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text('Toque numa marcação para ver o detalhe.',
                      style: TextStyle(color: Colors.white60, fontSize: 12)),
                ),
              const SizedBox(height: 16),

              // Índice de Saúde + resumo
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F1F35),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.white12),
                ),
                child: Column(children: [
                  HealthGauge(r.score),
                  const SizedBox(height: 14),
                  Text(r.resumo, textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.white, fontSize: 14)),
                ]),
              ),
              const SizedBox(height: 16),

              if (r.id != null) ..._acoes(anomalias.isNotEmpty),

              const SizedBox(height: 8),
              if (anomalias.isEmpty)
                _semAnomalia()
              else ...[
                Text('${anomalias.length} anomalia(s) detectada(s)',
                    style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                for (final (i, a) in anomalias.indexed)
                  _AnomaliaCard(
                    key: _chaves[i],
                    numero: i + 1,
                    anomalia: a,
                    aberta: _selecionada == i,
                    onTap: () => _selecionar(i),
                  ),
              ],
              const SizedBox(height: 8),
              Center(
                child: Text('Análise: ${r.modelo}',
                    style: const TextStyle(color: Colors.white38, fontSize: 11)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _acoes(bool temAnomalia) => [
        if (temAnomalia)
          SizedBox(
            width: double.infinity,
            height: 50,
            child: ElevatedButton.icon(
              onPressed: _abrirOcorrencia,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFF59E0B),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              icon: const Icon(Icons.add_alert_outlined, color: Colors.white, size: 20),
              label: const Text('Abrir ocorrência com este resultado',
                  style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ),
        const SizedBox(height: 10),
        Row(children: [
          Expanded(
            child: OutlinedButton.icon(
              onPressed: (_validado || _validando) ? null : _validar,
              style: _estiloSecundario(_validado ? const Color(0xFF22C55E) : null),
              icon: _validando
                  ? const SizedBox(width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white70))
                  : Icon(_validado ? Icons.verified : Icons.check, size: 18,
                      color: _validado ? const Color(0xFF22C55E) : Colors.white),
              label: Text(_validado ? 'Laudo validado' : 'Validar laudo',
                  style: TextStyle(color: _validado ? const Color(0xFF22C55E) : Colors.white, fontSize: 14)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Builder(
              builder: (botao) => OutlinedButton.icon(
                onPressed: _baixandoPdf ? null : () => _compartilharLaudo(botao),
                style: _estiloSecundario(null),
                icon: _baixandoPdf
                    ? const SizedBox(width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white70))
                    : const Icon(Icons.ios_share, size: 18, color: Colors.white),
                label: const Text('Laudo PDF', style: TextStyle(color: Colors.white, fontSize: 14)),
              ),
            ),
          ),
        ]),
        const SizedBox(height: 20),
      ];

  ButtonStyle _estiloSecundario(Color? cor) => OutlinedButton.styleFrom(
        minimumSize: const Size.fromHeight(46),
        side: BorderSide(color: cor ?? Colors.white24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      );

  Widget _semAnomalia() => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF22C55E).withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF22C55E).withValues(alpha: 0.25)),
        ),
        child: const Column(children: [
          Icon(Icons.check_circle_outline, color: Color(0xFF22C55E), size: 40),
          SizedBox(height: 12),
          Text('Nenhuma anomalia visível',
              style: TextStyle(color: Color(0xFF22C55E), fontSize: 15, fontWeight: FontWeight.w600)),
          SizedBox(height: 4),
          Text('O equipamento parece limpo, íntegro e bem conservado nesta foto.',
              textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 13)),
        ]),
      );
}

/// Foto com as caixas das anomalias (posição em % da imagem, calculada pelo servidor).
class _FotoComAnomalias extends StatefulWidget {
  final File foto;
  final List<Anomalia> anomalias;
  final int? selecionada;
  final ValueChanged<int> onTocar;

  const _FotoComAnomalias({
    required this.foto,
    required this.anomalias,
    required this.selecionada,
    required this.onTocar,
  });

  @override
  State<_FotoComAnomalias> createState() => _FotoComAnomaliasState();
}

class _FotoComAnomaliasState extends State<_FotoComAnomalias> {
  double? _proporcao;   // largura/altura real da foto: as caixas precisam da imagem inteira, sem corte

  @override
  void initState() {
    super.initState();
    widget.foto.readAsBytes().then(decodeImageFromList).then((img) {
      if (mounted) setState(() => _proporcao = img.width / img.height);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_proporcao == null) {
      return Container(
        height: 220,
        decoration: BoxDecoration(color: const Color(0xFF0F1F35), borderRadius: BorderRadius.circular(12)),
        alignment: Alignment.center,
        child: const CircularProgressIndicator(color: Color(0xFF0EA5E9), strokeWidth: 2),
      );
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: AspectRatio(
        aspectRatio: _proporcao!,
        child: LayoutBuilder(builder: (context, c) {
          return Stack(children: [
            Positioned.fill(child: Image.file(widget.foto, fit: BoxFit.fill)),
            for (final (i, a) in widget.anomalias.indexed)
              Positioned(
                left: a.left / 100 * c.maxWidth,
                top: a.top / 100 * c.maxHeight,
                width: (a.width / 100 * c.maxWidth).clamp(20.0, c.maxWidth),
                height: (a.height / 100 * c.maxHeight).clamp(20.0, c.maxHeight),
                child: _Caixa(
                  numero: i + 1,
                  cor: corDaSeveridade(a.severidade),
                  ativa: widget.selecionada == i,
                  apagada: widget.selecionada != null && widget.selecionada != i,
                  onTap: () => widget.onTocar(i),
                ),
              ),
          ]);
        }),
      ),
    );
  }
}

class _Caixa extends StatelessWidget {
  final int numero;
  final Color cor;
  final bool ativa;
  final bool apagada;
  final VoidCallback onTap;

  const _Caixa({required this.numero, required this.cor, required this.ativa,
      required this.apagada, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: 'Anomalia $numero',
      child: GestureDetector(
        behavior: HitTestBehavior.translucent,
        onTap: onTap,
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 200),
          opacity: apagada ? 0.35 : 1,
          child: Container(
            decoration: BoxDecoration(
              color: cor.withValues(alpha: ativa ? 0.22 : 0.08),
              border: Border.all(color: cor, width: ativa ? 3 : 2),
              borderRadius: BorderRadius.circular(4),
            ),
            alignment: Alignment.topLeft,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              color: cor,
              child: Text('$numero',
                  style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
            ),
          ),
        ),
      ),
    );
  }
}

class _AnomaliaCard extends StatelessWidget {
  final int numero;
  final Anomalia anomalia;
  final bool aberta;
  final VoidCallback onTap;

  const _AnomaliaCard({super.key, required this.numero, required this.anomalia,
      required this.aberta, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final a = anomalia;
    final cor = corDaSeveridade(a.severidade);
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0F1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: cor.withValues(alpha: aberta ? 0.9 : 0.3), width: aberta ? 1.5 : 1),
      ),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(
                  width: 28,
                  height: 28,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(color: cor, shape: BoxShape.circle),
                  child: Text('$numero',
                      style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(a.rotulo,
                        style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 2),
                    Text(a.componente, style: const TextStyle(color: Colors.white60, fontSize: 13)),
                  ]),
                ),
                SeverityChip(a.severidade, small: true),
                const SizedBox(width: 4),
                Icon(aberta ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    color: Colors.white54, size: 20),
              ]),
              if (aberta) ...[
                const Divider(color: Colors.white12, height: 24),
                _info('O que foi visto', a.descricao),
                if (a.causaProvavel.isNotEmpty) _info('Possível causa', a.causaProvavel),
                _info('O que fazer', a.recomendacao),
                Text('Confiança da IA: ${(a.confianca * 100).round()}%',
                    style: const TextStyle(color: Colors.white54, fontSize: 12)),
              ],
            ]),
          ),
        ),
      ),
    );
  }

  Widget _info(String rotulo, String texto) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(rotulo,
              style: const TextStyle(color: Colors.white60, fontSize: 12, fontWeight: FontWeight.w600)),
          const SizedBox(height: 3),
          Text(texto, style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.35)),
        ]),
      );
}
