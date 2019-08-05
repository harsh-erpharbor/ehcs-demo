odoo.define('ehcs_edit_chatter_message.ChatThreadCustom', function (require) {
"use strict";


var Thread = require('mail.ChatThread');
var core = require('web.core');
var QWeb = core.qweb;
var ajax = require('web.ajax');
var rpc = require('web.rpc');


Thread.include({
    events: {
        "click a": "on_click_redirect",
        "click img": "on_click_redirect",
        "click strong": "on_click_redirect",
        "click .o_thread_show_more": "on_click_show_more",
        "click .o_attachment_download": "_onAttachmentDownload",
        "click .o_attachment_view": "_onAttachmentView",
        "click .o_thread_message_needaction": function (event) {
            var message_id = $(event.currentTarget).data('message-id');
            this.trigger("mark_as_read", message_id);
        },
        "click .o_thread_message_star": function (event) {
            var message_id = $(event.currentTarget).data('message-id');
            this.trigger("toggle_star_status", message_id);
        },
        "click .fa-trash": function (event) {
            var message_id = $(event.currentTarget).data('message-id');
            var self = this;
            rpc.query({
                model: 'mail.message',
                method: 'unlink',
                args: [[message_id]],
            })
            .then(function (result){
                location.reload()
            });
        },
        "click .fa-edit": function (event) {
            var message_id = $(event.currentTarget).data('message-id');
            var self = this;
            ajax.jsonRpc('/get_message_details', 'call', {'message_id': message_id}).done(function() {
                }).then(function (message_details) {
                    self.$el.append(QWeb.render('view_chatter_message_template', {'msg_details': message_details, 'msg_id': message_id,}))
                    $("#ViewMessageModal").modal();
                    var originalModal = $('#ViewMessageModal').clone();
                    $(document).on('hidden.bs.modal', function () {
                        $('#ViewMessageModal').remove();
                        var myClone = originalModal.clone();
                        $('body').append(myClone);
                    });
                    return ;
                })
        },
        "click .btn-success": function (event) {
            var msg = document.getElementById('text_message').value;
            var msg_id = parseInt(document.getElementById('text_message_id').value);
            var self = this;
            var view = self.getParent();
            rpc.query({
                model: 'mail.message',
                method: 'write',
                args: [[msg_id], {'body': msg}],
            })
            .then(function (result){
                location.reload()
            });
        },
        "click .o_thread_message_reply": function (event) {
            this.selected_id = $(event.currentTarget).data('message-id');
            this.$('.o_thread_message').removeClass('o_thread_selected_message');
            this.$('.o_thread_message[data-message-id="' + this.selected_id + '"]')
                .addClass('o_thread_selected_message');
            this.trigger('select_message', this.selected_id);
            event.stopPropagation();
        },
        "click .oe_mail_expand": function (event) {
            event.preventDefault();
            var $message = $(event.currentTarget).parents('.o_thread_message');
            $message.addClass('o_message_expanded');
            this.expanded_msg_ids.push($message.data('message-id'));
        },
        "click .o_thread_message": function (event) {
            $(event.currentTarget).toggleClass('o_thread_selected_message');
        },
        "click": function () {
            if (this.selected_id) {
                this.unselect();
                this.trigger('unselect_message');
            }
        },
    },

})
});