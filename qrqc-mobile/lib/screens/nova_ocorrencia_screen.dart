import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';

const _fundo = Color(0xFF0A1628);
const _cartao = Color(0xFF0F1F35);
const _destaque = Color(0xFFF59E0B);
const _vermelho = Color(0xFFEF4444);
const _verde = Color(0xFF22C55E);

const _iconeSintoma = <String, IconData>{
  'vazamento': Icons.water_drop_outlined,
  'ruido': Icons.volume_up_outlined,
  'vibracao': Icons.vibration,
  'aquecimento': Icons.thermostat,
  'folga': Icons.swap_horiz,
  'medida': Icons.straighten,
  'travamento': Icons.lock_outline,
  'quebra': Icons.broken_image_outlined,
  'nao_liga': Icons.power_settings_new,
  'desarma': Icons.bolt,
  'alarme': Icons.warning_amber_outlined,
  'intermitente': Icons.signal_cellular_alt,
  'cabo': Icons.cable,
  'nao_atua': Icons.pan_tool_outlined,
  'danificado': Icons.report_problem_outlined,
  'outro': Icons.more_horiz,
};

/// Registro guiado, igual ao da web: máquina → peça do CAD → sintoma → parou? risco?
/// O impacto e o tipo saem das respostas (o servidor aplica a mesma regra).
/// Pode vir preenchida a partir de uma inspeção do Sensor Visual.
class NovaOcorrenciaScreen extends StatefulWidget {
  final int? maquinaId;
  final String? componenteId;
  final String texto;
  final bool risco;
  final int? inspecaoId;

  const NovaOcorrenciaScreen({
    super.key,
    this.maquinaId,
    this.componenteId,
    this.texto = '',
    this.risco = false,
    this.inspecaoId,
  });

  @override
  State<NovaOcorrenciaScreen> createState() => _NovaOcorrenciaScreenState();
}

class _NovaOcorrenciaScreenState extends State<NovaOcorrenciaScreen> {
  final _api = ApiService();
  final _textoCtrl = TextEditingController();
  final _alarmeCtrl = TextEditingController();

  List<Maquina> _maquinas = [];
  List<Componente> _componentes = [];
  List<Sintoma> _sintomas = [];
  Maquina? _maquina;
  Componente? _peca;
  Sintoma? _sintoma;
  bool? _parada;
  bool? _risco;
  bool _carregando = true;
  bool _carregandoPecas = false;
  bool _carregandoSintomas = false;
  bool _salvando = false;
  String? _erro;

  @override
  void initState() {
    super.initState();
    // Texto vindo da inspeção pode passar do limite do campo (2000): corta com reticências
    _textoCtrl.text = widget.texto.length > 2000 ? '${widget.texto.substring(0, 1999)}…' : widget.texto;
    if (widget.risco) _risco = true;
    _textoCtrl.addListener(() => setState(() {}));
    _carregarMaquinas();
  }

  @override
  void dispose() {
    _textoCtrl.dispose();
    _alarmeCtrl.dispose();
    super.dispose();
  }

  Future<void> _carregarMaquinas() async {
    setState(() { _carregando = true; _erro = null; });
    try {
      final lista = await _api.getMaquinas();
      if (!mounted) return;
      setState(() => _maquinas = lista);
      final pre = lista.where((m) => m.id == widget.maquinaId).firstOrNull;
      if (pre != null) await _escolherMaquina(pre, pecaInicial: widget.componenteId);
    } catch (e) {
      if (mounted) setState(() => _erro = e.toString());
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  Future<void> _escolherMaquina(Maquina m, {String? pecaInicial}) async {
    setState(() {
      _maquina = m;
      _peca = null;
      _sintoma = null;
      _componentes = [];
      _sintomas = [];
      _carregandoPecas = true;
    });
    try {
      final pecas = await _api.getComponentes(m.id);
      if (!mounted || _maquina?.id != m.id) return;
      setState(() => _componentes = pecas);
      final pre = pecas.where((p) => p.id == pecaInicial).firstOrNull;
      if (pre != null) await _escolherPeca(pre);
    } catch (e) {
      _avisar(e.toString());
    } finally {
      if (mounted) setState(() => _carregandoPecas = false);
    }
  }

  Future<void> _escolherPeca(Componente p) async {
    setState(() {
      _peca = p;
      _sintoma = null;
      _sintomas = [];
      _carregandoSintomas = true;
    });
    try {
      final lista = await _api.getSintomas(_maquina!.id, p.id);
      if (mounted && _peca?.id == p.id) setState(() => _sintomas = lista);
    } catch (e) {
      _avisar(e.toString());
    } finally {
      if (mounted) setState(() => _carregandoSintomas = false);
    }
  }

  // ── Regras (as mesmas do servidor) ──────────────────────────────────────
  bool get _textoObrigatorio => _sintoma?.id == 'outro';

  List<String> get _faltando => [
        if (_maquina == null) 'a máquina',
        if (_peca == null) 'a peça',
        if (_sintoma == null) 'o que está acontecendo',
        if (_parada == null) 'se a máquina parou',
        if (_risco == null) 'se há risco',
        if (_textoObrigatorio && _textoCtrl.text.trim().length < 5) 'a descrição',
      ];

  String get _impacto => (_parada == true || _risco == true) ? 'Alto' : 'Médio';

  Future<void> _registrar() async {
    if (_faltando.isNotEmpty || _salvando) return;
    setState(() => _salvando = true);
    try {
      final id = await _api.criarOcorrencia({
        'maquina_id': _maquina!.id,
        'componente_apontado': _peca!.id,
        'sintoma': _sintoma!.id,
        'maquina_parada': _parada,
        'risco_pessoas': _risco,
        'texto': _textoCtrl.text.trim(),
        'codigo_alarme': _alarmeCtrl.text.trim(),
        if (widget.inspecaoId != null) 'inspecao_id': widget.inspecaoId,
      });
      if (!mounted) return;
      Navigator.pop(context, id);
    } catch (e) {
      _avisar(e.toString());
    } finally {
      if (mounted) setState(() => _salvando = false);
    }
  }

  void _avisar(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: _vermelho,
      behavior: SnackBarBehavior.floating,
    ));
  }

  // ── Tela ────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _fundo,
      appBar: AppBar(
        backgroundColor: _fundo,
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.white, size: 22),
          tooltip: 'Cancelar',
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Nova ocorrência'),
      ),
      body: _carregando
          ? const Center(child: CircularProgressIndicator(color: _destaque, strokeWidth: 2))
          : _erro != null
              ? _falha()
              : Column(
                  children: [
                    Expanded(
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                        children: [
                          if (widget.inspecaoId != null) _faixaInspecao(),
                          _etapaMaquina(),
                          if (_maquina != null) _etapaPeca(),
                          if (_peca != null) _etapaSintoma(),
                        ],
                      ),
                    ),
                    if (_peca != null) _barraEnviar(),
                  ],
                ),
    );
  }

  Widget _falha() => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.cloud_off_outlined, color: Colors.white54, size: 40),
            const SizedBox(height: 12),
            Text(_erro!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70, fontSize: 14)),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: _carregarMaquinas, child: const Text('Tentar de novo')),
          ]),
        ),
      );

  Widget _faixaInspecao() => Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF0EA5E9).withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFF0EA5E9).withValues(alpha: 0.3)),
        ),
        child: Row(children: [
          const Icon(Icons.camera_alt_outlined, color: Color(0xFF0EA5E9), size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text('A partir da inspeção por foto nº ${widget.inspecaoId}',
                style: const TextStyle(color: Colors.white, fontSize: 13)),
          ),
        ]),
      );

  Widget _titulo(String numero, String texto, {Widget? acao}) => Padding(
        padding: const EdgeInsets.only(top: 18, bottom: 10),
        child: Row(children: [
          Container(
            width: 22,
            height: 22,
            alignment: Alignment.center,
            decoration: const BoxDecoration(color: _destaque, shape: BoxShape.circle),
            child: Text(numero, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(texto, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
          ),
          ?acao,
        ]),
      );

  Widget _trocar(VoidCallback onTap) => TextButton.icon(
        onPressed: onTap,
        icon: const Icon(Icons.sync, size: 16, color: _destaque),
        label: const Text('Trocar', style: TextStyle(color: _destaque, fontSize: 13)),
      );

  Widget _etapaMaquina() {
    if (_maquina != null) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _titulo('1', 'Máquina', acao: _trocar(() => setState(() {
              _maquina = null;
              _peca = null;
              _sintoma = null;
            }))),
        _cartaoEscolhido(Icons.precision_manufacturing_outlined, _maquina!.nome, _maquina!.setor),
      ]);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _titulo('1', 'Qual máquina?'),
      if (_maquinas.isEmpty)
        const Text('Nenhuma máquina com modelo CAD 3D cadastrada.',
            style: TextStyle(color: Colors.white70, fontSize: 14)),
      for (final m in _maquinas)
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Material(
            color: _cartao,
            borderRadius: BorderRadius.circular(12),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () => _escolherMaquina(m),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                child: Row(children: [
                  const Icon(Icons.precision_manufacturing_outlined, color: _destaque, size: 22),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(m.nome, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
                      if (m.setor.isNotEmpty)
                        Text(m.setor, style: const TextStyle(color: Colors.white60, fontSize: 13)),
                    ]),
                  ),
                  const Icon(Icons.chevron_right, color: Colors.white38),
                ]),
              ),
            ),
          ),
        ),
    ]);
  }

  Widget _etapaPeca() {
    if (_peca != null) {
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _titulo('2', 'Peça', acao: _trocar(() => setState(() {
              _peca = null;
              _sintoma = null;
            }))),
        _cartaoEscolhido(Icons.location_on_outlined, _peca!.nome, _peca!.descricao),
      ]);
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _titulo('2', 'Onde está o problema?'),
      if (_carregandoPecas)
        const Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: CircularProgressIndicator(color: _destaque, strokeWidth: 2)),
        )
      else
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final p in _componentes) _chip(p.nome, null, false, () => _escolherPeca(p)),
        ]),
    ]);
  }

  Widget _etapaSintoma() => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _titulo('3', 'O que está acontecendo?'),
        if (_carregandoSintomas)
          const Padding(
            padding: EdgeInsets.all(16),
            child: Center(child: CircularProgressIndicator(color: _destaque, strokeWidth: 2)),
          )
        else
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final s in _sintomas)
              _chip(s.nome, _iconeSintoma[s.id] ?? Icons.help_outline, _sintoma?.id == s.id,
                  () => setState(() => _sintoma = s)),
          ]),
        const SizedBox(height: 20),
        _simNao('A máquina parou?', _parada, (v) => setState(() => _parada = v)),
        const SizedBox(height: 12),
        _simNao('Há risco para pessoas?', _risco, (v) => setState(() => _risco = v)),
        const SizedBox(height: 20),
        Text(_textoObrigatorio ? 'Conte o que você viu (obrigatório)' : 'Conte o que você viu (opcional)',
            style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500)),
        const SizedBox(height: 8),
        TextField(
          controller: _textoCtrl,
          maxLines: widget.texto.isNotEmpty ? 6 : 3,
          maxLength: 2000,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: _deco('Ex.: óleo escorrendo pela haste ao fim do ciclo'),
        ),
        Theme(
          data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
          child: ExpansionTile(
            tilePadding: EdgeInsets.zero,
            iconColor: Colors.white70,
            collapsedIconColor: Colors.white70,
            title: const Text('Código de alarme no painel (opcional)',
                style: TextStyle(color: Colors.white70, fontSize: 13)),
            children: [
              TextField(
                controller: _alarmeCtrl,
                maxLength: 40,
                style: const TextStyle(color: Colors.white, fontSize: 14),
                decoration: _deco('Ex.: 50296'),
              ),
            ],
          ),
        ),
      ]);

  Widget _cartaoEscolhido(IconData icone, String titulo, String sub) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: _destaque.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _destaque.withValues(alpha: 0.35)),
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(icone, color: _destaque, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(titulo, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
              if (sub.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(sub, style: const TextStyle(color: Colors.white60, fontSize: 13)),
              ],
            ]),
          ),
        ]),
      );

  Widget _chip(String texto, IconData? icone, bool ativo, VoidCallback onTap) => Material(
        color: ativo ? _destaque : _cartao,
        shape: StadiumBorder(side: BorderSide(color: ativo ? _destaque : Colors.white24)),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: 44),     // alvo de toque confortável
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                if (icone != null) ...[
                  Icon(icone, size: 18, color: ativo ? Colors.white : _destaque),
                  const SizedBox(width: 8),
                ],
                Flexible(
                  child: Text(texto,
                      style: TextStyle(color: ativo ? Colors.white : Colors.white, fontSize: 14,
                          fontWeight: ativo ? FontWeight.w600 : FontWeight.w400)),
                ),
              ]),
            ),
          ),
        ),
      );

  Widget _simNao(String pergunta, bool? valor, ValueChanged<bool> onChanged) => Row(children: [
        Expanded(child: Text(pergunta, style: const TextStyle(color: Colors.white, fontSize: 15))),
        SegmentedButton<bool>(
          showSelectedIcon: false,
          emptySelectionAllowed: true,
          segments: const [
            ButtonSegment(value: true, label: Text('Sim')),
            ButtonSegment(value: false, label: Text('Não')),
          ],
          selected: valor == null ? {} : {valor},
          onSelectionChanged: (s) { if (s.isNotEmpty) onChanged(s.first); },
          style: ButtonStyle(
            foregroundColor: WidgetStateProperty.resolveWith((st) =>
                st.contains(WidgetState.selected) ? Colors.white : Colors.white70),
            backgroundColor: WidgetStateProperty.resolveWith((st) => !st.contains(WidgetState.selected)
                ? _cartao
                : (valor == true ? _vermelho : _verde)),
            side: const WidgetStatePropertyAll(BorderSide(color: Colors.white24)),
          ),
        ),
      ]);

  Widget _barraEnviar() {
    final falta = _faltando;
    return Container(
      padding: EdgeInsets.fromLTRB(20, 12, 20, 12 + MediaQuery.of(context).padding.bottom),
      decoration: const BoxDecoration(
        color: _cartao,
        border: Border(top: BorderSide(color: Colors.white12)),
      ),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Row(children: [
          Icon(falta.isEmpty ? Icons.check_circle_outline : Icons.info_outline,
              size: 16, color: falta.isEmpty ? _verde : Colors.white60),
          const SizedBox(width: 8),
          Expanded(
            child: falta.isEmpty
                ? Text.rich(TextSpan(style: const TextStyle(color: Colors.white70, fontSize: 13), children: [
                    const TextSpan(text: 'Impacto '),
                    TextSpan(text: _impacto,
                        style: TextStyle(color: _impacto == 'Alto' ? _vermelho : _destaque, fontWeight: FontWeight.w700)),
                    if (_risco == true) const TextSpan(text: ' · registrada como Segurança'),
                  ]))
                : Text('Falta informar ${falta.join(', ')}.',
                    style: const TextStyle(color: Colors.white60, fontSize: 13)),
          ),
        ]),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton.icon(
            onPressed: falta.isEmpty && !_salvando ? _registrar : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: _destaque,
              disabledBackgroundColor: _destaque.withValues(alpha: 0.3),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            icon: _salvando
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.send, color: Colors.white, size: 18),
            label: Text(_salvando ? 'Registrando…' : 'Registrar ocorrência',
                style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
          ),
        ),
      ]),
    );
  }

  InputDecoration _deco(String dica) => InputDecoration(
        hintText: dica,
        hintStyle: const TextStyle(color: Colors.white38, fontSize: 14),
        counterStyle: const TextStyle(color: Colors.white38),
        filled: true,
        fillColor: _cartao,
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Colors.white24),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: _destaque, width: 1.5),
        ),
      );
}
