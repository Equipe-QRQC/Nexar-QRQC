import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qrqc_mobile/models/models.dart';
import 'package:qrqc_mobile/screens/result_doc_screen.dart';

Future<void> _abrir(WidgetTester tester, Map<String, dynamic> json) async {
  tester.view.physicalSize = const Size(1080, 2400);
  addTearDown(tester.view.resetPhysicalSize);
  await tester.pumpWidget(
    MaterialApp(
      home: ResultDocScreen(resultado: ResultadoDocumento.fromJson(json)),
    ),
  );
}

void main() {
  testWidgets(
    'PT bem preenchida com NR-10 vencida aparece BLOQUEADA, nunca "sem problemas"',
    (tester) async {
      await _abrir(tester, {
        'status': 'bloqueado',
        'problemas': [],
        'score': 40,
        'resumo': 'Preenchido corretamente.',
        'modelo': 'gpt-4o',
        'conferencia': {
          'conferencias': [
            {
              'categoria': 'habilitacao',
              'severidade': 'alto',
              'titulo': 'Marcos Pereira: NR-10 vencido em 01/10/2026',
              'descricao':
                  'Não pode executar este serviço até renovar o NR-10.',
            },
          ],
        },
      });
      expect(find.text('BLOQUEADO'), findsOneWidget);
      expect(
        find.text('Marcos Pereira: NR-10 vencido em 01/10/2026'),
        findsOneWidget,
      );
      expect(find.text('Documento sem problemas detectados'), findsNothing);
    },
  );

  testWidgets('Documento aprovado sem pendências mostra o estado vazio', (
    tester,
  ) async {
    await _abrir(tester, {
      'status': 'aprovado',
      'problemas': [],
      'score': 100,
      'resumo': 'Análise concluída.',
      'modelo': 'gpt-4o',
      'conferencia': {'conferencias': []},
    });
    expect(find.text('APROVADO'), findsOneWidget);
    expect(find.text('Documento sem problemas detectados'), findsOneWidget);
  });

  testWidgets('Campos numéricos ou nulos vindos da IA não quebram a tela', (
    tester,
  ) async {
    await _abrir(tester, {
      'status': 'pendencias',
      'problemas': [
        {
          'tipo': 'dado_faltante',
          'campo': 7,
          'descricao': null,
          'sugestao': 3.5,
          'severidade': 'alto',
        },
      ],
      'score': 70.0,
      'resumo': 'Faltam assinaturas.',
      'modelo': 'gpt-4o',
    });
    expect(find.text('COM PENDÊNCIAS'), findsOneWidget);
    expect(find.text('1 problema(s) encontrado(s)'), findsOneWidget);
  });
}
