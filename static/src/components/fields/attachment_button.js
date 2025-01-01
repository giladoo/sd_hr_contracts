/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class AddAttachmentButton extends Component {
    static template = "sd_hr.AddAttachmentButton";
    onClick(ev){
        let fileUploader = ev.target.ownerDocument.querySelector('.o-mail-Chatter-fileUploader')
        fileUploader ? fileUploader.click() : '';
    }
}

export const addAttachmentButton = {
    component: AddAttachmentButton,
    displayName: _t("Add Attachment"),
    supportedTypes: ["char"],
};

registry.category("fields").add("attachment_button", addAttachmentButton);
