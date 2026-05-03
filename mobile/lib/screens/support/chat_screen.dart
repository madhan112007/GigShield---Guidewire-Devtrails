import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:susanoo/providers/app_providers.dart';
import 'package:susanoo/services/chat_service.dart';
import 'package:susanoo/theme/app_theme.dart';

// ── State ─────────────────────────────────────────────────────────────────────

class _ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final bool isEscalated;
  final String? conversationId;
  final String? error;

  const _ChatState({
    this.messages = const [],
    this.isLoading = false,
    this.isEscalated = false,
    this.conversationId,
    this.error,
  });

  _ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    bool? isEscalated,
    String? conversationId,
    String? error,
  }) =>
      _ChatState(
        messages: messages ?? this.messages,
        isLoading: isLoading ?? this.isLoading,
        isEscalated: isEscalated ?? this.isEscalated,
        conversationId: conversationId ?? this.conversationId,
        error: error,
      );
}

class _ChatNotifier extends StateNotifier<_ChatState> {
  final ChatService _service;
  _ChatNotifier(this._service) : super(const _ChatState()) {
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final history = await _service.getHistory();
      if (history.isNotEmpty) {
        state = state.copyWith(messages: history);
      }
    } catch (_) {}
  }

  Future<void> send(String text) async {
    if (text.trim().isEmpty) return;

    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      senderType: 'user',
      content: text.trim(),
      suggestedActions: [],
      shouldEscalate: false,
      createdAt: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMsg],
      isLoading: true,
      error: null,
    );

    try {
      final response = await _service.sendMessage(
        text.trim(),
        conversationId: state.conversationId,
      );

      final botMsg = ChatMessage(
        id: response.messageId,
        senderType: 'bot',
        content: response.answer,
        suggestedActions: response.suggestedActions,
        shouldEscalate: response.shouldEscalate,
        agentUsed: response.agentUsed,
        language: response.language,
        createdAt: DateTime.now(),
      );

      state = state.copyWith(
        messages: [...state.messages, botMsg],
        isLoading: false,
        isEscalated: response.shouldEscalate,
        conversationId: response.conversationId,
      );
    } catch (e) {
      final errMsg = ChatMessage(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        senderType: 'bot',
        content: 'Abhi system busy hai. Thodi der mein try karein.',
        suggestedActions: ['Contact Support'],
        shouldEscalate: false,
        createdAt: DateTime.now(),
      );
      state = state.copyWith(
        messages: [...state.messages, errMsg],
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> sendFeedback(String messageId, int rating) async {
    try {
      await _service.sendFeedback(messageId, rating);
    } catch (_) {}
  }
}

final _chatProvider =
    StateNotifierProvider.autoDispose<_ChatNotifier, _ChatState>((ref) {
  final api = ref.watch(apiServiceProvider);
  return _ChatNotifier(ChatService(api));
});

// ── Screen ────────────────────────────────────────────────────────────────────

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(_chatProvider.notifier).send(text);
    _scrollToBottom();
  }

  void _sendQuickReply(String text) {
    ref.read(_chatProvider.notifier).send(text);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(_chatProvider);

    ref.listen<_ChatState>(_chatProvider, (_, next) {
      if (!next.isLoading) _scrollToBottom();
    });

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: _buildAppBar(chatState.isEscalated),
      body: Column(
        children: [
          if (chatState.isEscalated) _EscalationBanner(),
          Expanded(
            child: chatState.messages.isEmpty && !chatState.isLoading
                ? _WelcomeView(onQuickTap: _sendQuickReply)
                : _MessageList(
                    messages: chatState.messages,
                    isLoading: chatState.isLoading,
                    scrollController: _scrollController,
                    onQuickReply: _sendQuickReply,
                    onFeedback: (id, rating) =>
                        ref.read(_chatProvider.notifier).sendFeedback(id, rating),
                  ),
          ),
          _InputBar(
            controller: _controller,
            focusNode: _focusNode,
            isLoading: chatState.isLoading,
            onSend: _send,
          ),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar(bool isEscalated) {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      leading: const BackButton(color: AppTheme.textPrimary),
      title: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.smart_toy_rounded,
                color: Colors.white, size: 20),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('SUSHI',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary)),
              Row(
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: isEscalated ? AppTheme.warning : AppTheme.success,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    isEscalated ? 'Connecting to agent...' : 'Susanoo Support',
                    style: const TextStyle(
                        fontSize: 11, color: AppTheme.textSecondary),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Welcome view ──────────────────────────────────────────────────────────────

class _WelcomeView extends StatelessWidget {
  final void Function(String) onQuickTap;
  const _WelcomeView({required this.onQuickTap});

  static const _quickReplies = [
    'Mera claim status kya hai?',
    'Payout kab aayega?',
    'Basic aur Pro mein kya difference hai?',
    'Active disruption hai kya?',
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 24),
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: AppTheme.primaryLight,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(Icons.smart_toy_rounded,
                color: AppTheme.primary, size: 40),
          ),
          const SizedBox(height: 16),
          const Text('Namaste! Main SUSHI hoon',
              style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Text(
            'Susanoo ka AI support assistant.\nClaim, payout, policy — sab ke liye yahan hoon.',
            textAlign: TextAlign.center,
            style:
                TextStyle(fontSize: 14, color: AppTheme.textSecondary, height: 1.5),
          ),
          const SizedBox(height: 32),
          const Align(
            alignment: Alignment.centerLeft,
            child: Text('Quick questions:',
                style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textSecondary)),
          ),
          const SizedBox(height: 12),
          ..._quickReplies.map((q) => _QuickReplyChip(
                label: q,
                onTap: () => onQuickTap(q),
              )),
        ],
      ),
    );
  }
}

class _QuickReplyChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _QuickReplyChip({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.divider),
        ),
        child: Row(
          children: [
            Expanded(
                child: Text(label,
                    style: const TextStyle(
                        fontSize: 14, color: AppTheme.textPrimary))),
            const Icon(Icons.arrow_forward_ios_rounded,
                size: 14, color: AppTheme.textHint),
          ],
        ),
      ),
    );
  }
}

// ── Message list ──────────────────────────────────────────────────────────────

class _MessageList extends StatelessWidget {
  final List<ChatMessage> messages;
  final bool isLoading;
  final ScrollController scrollController;
  final void Function(String) onQuickReply;
  final void Function(String, int) onFeedback;

  const _MessageList({
    required this.messages,
    required this.isLoading,
    required this.scrollController,
    required this.onQuickReply,
    required this.onFeedback,
  });

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      controller: scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: messages.length + (isLoading ? 1 : 0),
      itemBuilder: (context, i) {
        if (i == messages.length) return const _TypingIndicator();
        final msg = messages[i];
        return msg.isUser
            ? _UserBubble(message: msg)
            : _BotBubble(
                message: msg,
                onQuickReply: onQuickReply,
                onFeedback: onFeedback,
              );
      },
    );
  }
}

// ── User bubble ───────────────────────────────────────────────────────────────

class _UserBubble extends StatelessWidget {
  final ChatMessage message;
  const _UserBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: const BoxDecoration(
                color: AppTheme.primary,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                  bottomLeft: Radius.circular(18),
                  bottomRight: Radius.circular(4),
                ),
              ),
              child: Text(
                message.content,
                style: const TextStyle(
                    color: Colors.white, fontSize: 14, height: 1.4),
              ),
            ),
          ),
          const SizedBox(width: 8),
          const CircleAvatar(
            radius: 14,
            backgroundColor: AppTheme.primaryLight,
            child: Icon(Icons.person_rounded,
                size: 16, color: AppTheme.primary),
          ),
        ],
      ),
    );
  }
}

// ── Bot bubble ────────────────────────────────────────────────────────────────

class _BotBubble extends StatelessWidget {
  final ChatMessage message;
  final void Function(String) onQuickReply;
  final void Function(String, int) onFeedback;

  const _BotBubble({
    required this.message,
    required this.onQuickReply,
    required this.onFeedback,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.smart_toy_rounded,
                color: Colors.white, size: 16),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(4),
                      topRight: Radius.circular(18),
                      bottomLeft: Radius.circular(18),
                      bottomRight: Radius.circular(18),
                    ),
                    border: Border.all(color: AppTheme.divider),
                  ),
                  child: Text(
                    message.content,
                    style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 14,
                        height: 1.5),
                  ),
                ),
                if (message.suggestedActions.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: message.suggestedActions
                        .map((a) => _ActionChip(
                              label: a,
                              onTap: () => onQuickReply(a),
                            ))
                        .toList(),
                  ),
                ],
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(
                      _timeLabel(message.createdAt),
                      style: const TextStyle(
                          fontSize: 10, color: AppTheme.textHint),
                    ),
                    const SizedBox(width: 8),
                    _FeedbackRow(
                      messageId: message.id,
                      onFeedback: onFeedback,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _timeLabel(DateTime dt) {
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}

class _ActionChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _ActionChip({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.primaryLight,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
        ),
        child: Text(label,
            style: const TextStyle(
                fontSize: 12,
                color: AppTheme.primary,
                fontWeight: FontWeight.w500)),
      ),
    );
  }
}

class _FeedbackRow extends StatefulWidget {
  final String messageId;
  final void Function(String, int) onFeedback;
  const _FeedbackRow({required this.messageId, required this.onFeedback});

  @override
  State<_FeedbackRow> createState() => _FeedbackRowState();
}

class _FeedbackRowState extends State<_FeedbackRow> {
  int? _selected;

  @override
  Widget build(BuildContext context) {
    if (_selected != null) {
      return const Text('Thanks!',
          style: TextStyle(fontSize: 10, color: AppTheme.success));
    }
    return Row(
      children: [
        _FeedbackBtn(
            icon: Icons.thumb_up_rounded,
            onTap: () {
              setState(() => _selected = 5);
              widget.onFeedback(widget.messageId, 5);
            }),
        const SizedBox(width: 4),
        _FeedbackBtn(
            icon: Icons.thumb_down_rounded,
            onTap: () {
              setState(() => _selected = 1);
              widget.onFeedback(widget.messageId, 1);
            }),
      ],
    );
  }
}

class _FeedbackBtn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _FeedbackBtn({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Icon(icon, size: 14, color: AppTheme.textHint),
    );
  }
}

// ── Typing indicator ──────────────────────────────────────────────────────────

class _TypingIndicator extends StatefulWidget {
  const _TypingIndicator();

  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 800))
      ..repeat(reverse: true);
    _anim = Tween(begin: 0.3, end: 1.0).animate(_ctrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.smart_toy_rounded,
                color: Colors.white, size: 16),
          ),
          const SizedBox(width: 8),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppTheme.divider),
            ),
            child: FadeTransition(
              opacity: _anim,
              child: Row(
                children: List.generate(
                  3,
                  (i) => Container(
                    width: 6,
                    height: 6,
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    decoration: const BoxDecoration(
                      color: AppTheme.textHint,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Escalation banner ─────────────────────────────────────────────────────────

class _EscalationBanner extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: AppTheme.warning.withOpacity(0.1),
      child: Row(
        children: const [
          Icon(Icons.support_agent_rounded,
              color: AppTheme.warning, size: 18),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'Connecting to human support agent...',
              style: TextStyle(
                  fontSize: 13,
                  color: AppTheme.warning,
                  fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Input bar ─────────────────────────────────────────────────────────────────

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool isLoading;
  final VoidCallback onSend;

  const _InputBar({
    required this.controller,
    required this.focusNode,
    required this.isLoading,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 12,
        bottom: MediaQuery.of(context).viewInsets.bottom + 12,
      ),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: AppTheme.divider, width: 0.5)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              focusNode: focusNode,
              enabled: !isLoading,
              maxLines: 3,
              minLines: 1,
              textCapitalization: TextCapitalization.sentences,
              decoration: InputDecoration(
                hintText: 'Kuch poochna hai? Type karein...',
                hintStyle: const TextStyle(
                    color: AppTheme.textHint, fontSize: 14),
                filled: true,
                fillColor: AppTheme.surface,
                contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 10),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: AppTheme.divider),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: AppTheme.divider),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide:
                      const BorderSide(color: AppTheme.primary, width: 1.5),
                ),
              ),
              onSubmitted: (_) => onSend(),
            ),
          ),
          const SizedBox(width: 8),
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            child: isLoading
                ? const SizedBox(
                    width: 44,
                    height: 44,
                    child: Padding(
                      padding: EdgeInsets.all(10),
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppTheme.primary),
                    ),
                  )
                : GestureDetector(
                    onTap: onSend,
                    child: Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: AppTheme.primary,
                        borderRadius: BorderRadius.circular(22),
                      ),
                      child: const Icon(Icons.send_rounded,
                          color: Colors.white, size: 20),
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
