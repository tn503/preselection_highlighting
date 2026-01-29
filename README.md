# Blender mesh editmode preselection highlighting add-on.
Using only blender python API.

* Does not support Object Transform.
* Does not support X-ray mode.
* Does not support Ngon.
* Does not support Ctrl+Click.

## Usage:
1. Download op_preselection.py.
2. Install from Disk...
3. Push [Preselection] button in SpaceView3D header.

## Update:
January 15th, 2026.
* Add avoid bmesh update code.
* Fix incomplete selection restore.
* Does not support X-ray mode.

January 13th, 2026.
* Add Interval value for execute preselection.

## Appendix:
If you need more better performance, change Blender source codes.

* source/blender/editors/space_view3d/view3d_select.cc
* static wmOperatorStatus view3d_select_exec(bContext *C, wmOperator *op)

      if (obedit->type != OB_ARMATURE) {
        return OPERATOR_PASS_THROUGH | OPERATOR_CANCELLED;
      }
    
to

      if (obedit->type != OB_ARMATURE) {
        if (obedit && object_only == false) {
          if (obedit->type == OB_MESH) {
              RNA_int_get_array(op->ptr, "location", mval);
              view3d_operator_needs_gpu(C);
              BKE_object_update_select_id(CTX_data_main(C));
              SelectPick_Params params2 = ED_select_pick_params_from_operator(op->ptr);
              params2.sel_op = SEL_OP_AND;
              changed = EDBM_select_pick(C, mval, params2);
              return OPERATOR_FINISHED;
          }
        }
        return OPERATOR_PASS_THROUGH | OPERATOR_CANCELLED;
      }


* source/blender/editors/mesh/editmesh_select.cc
* bool EDBM_select_pick(bContext *C, const int mval[2], const SelectPick_Params &params)
  
      bool changed = false;
      bool found = unified_findnearest(&vc, bases, &base_index_active, &eve, &eed, &efa);
    
      if (params.sel_op == SEL_OP_SET) {

to
  
    bool changed = false;
    bool found = unified_findnearest(&vc, bases, &base_index_active, &eve, &eed, &efa);
    
    if (params.sel_op == SEL_OP_AND) {
      if (found) {
        Base *basact = bases[base_index_active];
        ED_view3d_viewcontext_init_object(&vc, basact->object);
        BMEditMesh *em = vc.em;
        
        EDBM_flag_disable_all(em, BM_ELEM_TAG);
        if (eve) BM_elem_flag_set(eve, BM_ELEM_TAG, true);
        if (eed) BM_elem_flag_set(eed, BM_ELEM_TAG, true);
        if (efa) BM_elem_flag_set(efa, BM_ELEM_TAG, true);
      }
      return false;
    }
    
    if (params.sel_op == SEL_OP_SET) {

So, this makes bpy.ops.view3d.select(location = xy, enumerate= True) in editmode set tag without selection change.
Check bmesh element .tag value and draw element in python script.
