export type Lookup={id:number;name:string}
export type Nib={id:string;description:string;material:Lookup;size:string|null;is_original:boolean}
export type Installation={id:string;nib_id:string;installed_on:string|null;removed_on:string|null;is_current:boolean}
export type Note={id:string;text:string;event_on:string|null;created_at:string;updated_at:string}
export type PenImage={id:string;url:string;thumbnail_url:string;caption:string|null;sort_order:number}
export type Pen={id:string;model:string;maker:Lookup;source:Lookup|null;acquired_on:string;acquired_on_approximate:boolean;disposed_on:string|null;disposed_on_approximate:boolean;purchase_price:string;currency:string;nibs:Nib[];installations:Installation[];notes:Note[];images:PenImage[]}
export type Report={summary:{count:number;total:string;average:string};makers:Array<{name:string;count:number;total:string;average:string}>;materials:Array<{name:string;count:number;total:string;average:string}>;quarterly:Array<{quarter:string;count:number;total:string}>;scatter:Array<{id:string;acquired_on:string;price:string;maker:string;model:string}>;pivot:Array<{description:string;material:string;total:string}>}
