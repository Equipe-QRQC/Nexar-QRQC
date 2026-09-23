import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import 'result_doc_screen.dart';

class DocScanScreen extends StatefulWidget {
  const DocScanScreen({super.key});
  @override
  State<DocScanScreen> createState() => _DocScanScreenState();
}

class _DocScanScreenState extends State<DocScanScreen> {
  final _picker = ImagePicker();
  File? _foto;
  bool _analisando = false;
  String _tipoDoc = '';

  static const _tipos = [
    'Formulário QRQC',
    'Ordem de serviço',
    'Relatório de inspeção',
    'Laudo técnico',
    'Planilha de manutenção',
    'Outro',
  ];

  Future<void> _capturar(ImageSource source) async {
    final xfile = await _picker.pickImage(
      source: source,
      maxWidth: 2400,
      maxHeight: 2400,
      imageQuality: 90,
    );
    if (xfile != null && mounted) {
      setState(() => _foto = File(xfile.path));
    }
  }

  Future<void> _analisar() async {
    if (_foto == null) return;
    setState(() => _analisando = true);
    try {
      final resultado = await ApiService().analisarDocumento(
        _foto!,
        tipoDocumento: _tipoDoc,
      );
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ResultDocScreen(resultado: resultado),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString()),
          backgroundColor: const Color(0xFFEF4444),
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _analisando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A1628),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A1628),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new,
              color: Colors.white, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Inspecionar Documento',
          style: TextStyle(color: Colors.white, fontSize: 16),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Descrição
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFF8B5CF6).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                      color: const Color(0xFF8B5CF6).withOpacity(0.2)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.auto_awesome,
                        color: Color(0xFF8B5CF6), size: 18),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'A Nexa IA encontra erros de cálculo, campos incompletos, inconsistências e dados incorretos.',
                        style: TextStyle(
                            color: Colors.white70, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Foto do documento
              GestureDetector(
                onTap: () => _showPickOptions(),
                child: Container(
                  height: 240,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F1F35),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _foto == null
                          ? Colors.white12
                          : const Color(0xFF8B5CF6).withOpacity(0.4),
                    ),
                  ),
                  child: _foto == null
                      ? const Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.document_scanner_outlined,
                                color: Colors.white24, size: 44),
                            SizedBox(height: 10),
                            Text(
                              'Fotografe o documento\nou escolha da galeria',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                  color: Colors.white38, fontSize: 13),
                            ),
                            SizedBox(height: 4),
                            Text(
                              'Para melhores resultados, iluminação\nuniforme e sem reflexos',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                  color: Colors.white24, fontSize: 11),
                            ),
                          ],
                        )
                      : Stack(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.file(_foto!,
                                  width: double.infinity,
                                  height: double.infinity,
                                  fit: BoxFit.cover),
                            ),
                            Positioned(
                              top: 8,
                              right: 8,
                              child: GestureDetector(
                                onTap: () =>
                                    setState(() => _foto = null),
                                child: Container(
                                  padding: const EdgeInsets.all(4),
                                  decoration: BoxDecoration(
                                    color: Colors.black54,
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: const Icon(Icons.close,
                                      color: Colors.white, size: 16),
                                ),
                              ),
                            ),
                          ],
                        ),
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _btn(Icons.camera_alt_outlined, 'Câmera',
                        () => _capturar(ImageSource.camera)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _btn(Icons.photo_library_outlined, 'Galeria',
                        () => _capturar(ImageSource.gallery)),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Tipo de documento
              const Text('Tipo de documento',
                  style: TextStyle(
                      color: Colors.white54,
                      fontSize: 12,
                      fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _tipos
                    .map((t) => ChoiceChip(
                          label: Text(t,
                              style: TextStyle(
                                fontSize: 12,
                                color: _tipoDoc == t
                                    ? Colors.white
                                    : Colors.white54,
                              )),
                          selected: _tipoDoc == t,
                          onSelected: (v) =>
                              setState(() => _tipoDoc = v ? t : ''),
                          selectedColor: const Color(0xFF8B5CF6),
                          backgroundColor: const Color(0xFF0F1F35),
                          side: BorderSide(
                            color: _tipoDoc == t
                                ? const Color(0xFF8B5CF6)
                                : Colors.white12,
                          ),
                          showCheckmark: false,
                        ))
                    .toList(),
              ),
              const SizedBox(height: 28),

              SizedBox(
                width: double.infinity,
                height: 52,
                child: ElevatedButton.icon(
                  onPressed: (_foto == null || _analisando) ? null : _analisar,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF8B5CF6),
                    disabledBackgroundColor:
                        const Color(0xFF8B5CF6).withOpacity(0.3),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                  ),
                  icon: _analisando
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2),
                        )
                      : const Icon(Icons.find_in_page_outlined,
                          color: Colors.white, size: 20),
                  label: Text(
                    _analisando ? 'Analisando…' : 'Inspecionar com Nexa IA',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showPickOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F1F35),
      shape: const RoundedRectangleBorder(
          borderRadius:
              BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt_outlined,
                  color: Color(0xFF8B5CF6)),
              title: const Text('Câmera',
                  style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _capturar(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined,
                  color: Color(0xFF8B5CF6)),
              title: const Text('Galeria',
                  style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _capturar(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _btn(IconData icon, String label, VoidCallback onTap) =>
      OutlinedButton.icon(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Colors.white12),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(vertical: 10),
        ),
        icon: Icon(icon, color: const Color(0xFF8B5CF6), size: 18),
        label: Text(label,
            style:
                const TextStyle(color: Colors.white70, fontSize: 13)),
      );
}
