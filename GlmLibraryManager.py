# -*- coding: utf-8 -*-
import json
import NodegraphAPI
import PackageSuperToolAPI

from Katana import Widgets

# 
import glmCharFileManager

ROOT_NODE = NodegraphAPI.GetRootNode()
GOLAEM_MESSAGE = 'GolaemCache \n'
KLF_MESSAGE = '\nGlmMasterSettings \n'

def create(layout, node):   
    # check
    check = pre_check(node)
    if not check:
        return
        
    # get data
    with open(layout, 'r') as f:
        data = json.load(f)
    items = data['items']
    # del image
    for item in items:
        del(item[u'image'])

    # count
    count = 0
    align_x_pos = get_align_x_pos(len(items))
    # merge node
    merge_node = glm_merge_node(node)
    merge_node_pos = NodegraphAPI.GetNodePosition(merge_node)
    
    # create golaem node    
    for item in items:
        golaem_node, gms_node = create_gol_set_nodes(item)
        # set default position
        NodegraphAPI.SetNodePosition(golaem_node, (merge_node_pos[0] + align_x_pos, merge_node_pos[1]+250))
        NodegraphAPI.SetNodePosition(gms_node, (merge_node_pos[0] + align_x_pos, merge_node_pos[1]+150))
        # connect node
        input_num = 'i' + str(count)
        merge_node.addInputPort(input_num).connect(gms_node.getOutputPort('o0')) # why name o0?
        # adding count
        count += 1
        align_x_pos += 250
    
        checking_golaem_data(golaem_node)
        checking_gms_data(gms_node)

    # message box
    if len(GOLAEM_MESSAGE+KLF_MESSAGE) <= 33:
        printInfo = "Done!!!\n"
        Widgets.MessageBox.Information('Info', printInfo, acceptText="Ok")        
    else:
        printInfo = GOLAEM_MESSAGE + KLF_MESSAGE   
        Widgets.MessageBox.Warning('Warning', printInfo, acceptText="Ok")
        print ('---------------------------------------------------------------')
        print ('--------------- GlmLibraryManager check message ---------------')
        print (printInfo)


def pre_check(node):
    port = node.getInputPort('i0')
    upstream_node = PackageSuperToolAPI.NodeUtils.GetUpstreamPort(port)

    info = True
    if upstream_node:
        printInfo = '''골렘 노드가 존재하는 것 같습니다. 그래도 다시 만드시겠습니까?
Ok를 누르면, 기존 노드들은 지워지고 새로운 노드들로 만들어 집니다.'''
        info = Widgets.MessageBox.Information('Info', printInfo, acceptText='Ok', cancelText='Cancel')
        if info == 1:
            info = None
        else:
            info = True
            del_nodes(node)
        
    return info
    

def upstream(node):
    ports = node.getInputPorts()

    for port in ports:
        upstream_node = PackageSuperToolAPI.NodeUtils.GetUpstreamPort(port)
        try:
            dep = upstream_node.getNode()
        except:
            continue
        NodegraphAPI.SetNodeSelected(dep, True)

        upstream(node=dep)
    slected_nodes = NodegraphAPI.GetAllSelectedNodes()
    return slected_nodes
    
        
def del_nodes(node):
    # deselect all
    all_node = NodegraphAPI.GetAllNodes()
    for an in all_node:
        NodegraphAPI.SetNodeSelected(an, False)

    # upstream
    upstream_list =  upstream(node)

    # delete
    parnet_list = []
    for ups in upstream_list:
        parent_node = ups.getParent()

        if parent_node.getName() == 'rootNode':
            ups.delete()
        else:
            if parent_node not in parnet_list:
                parnet_list.append(parent_node)
    # not selected group node
    for par in parnet_list:
        par.delete()


def create_gol_set_nodes(item):
    # get gscb data
    node_name = item[u'nodeName']
    crowd_fields = ';'.join(item[u'crowdFields'])
    cache_name = item[u'cacheName']
    cache_dir = item[u'cacheDir']
    character_files = item[u'characterFiles']
    enable_layout = item[u'enableLayout']
    layout_file = item[u'layoutFile']

    # create golaem cache
    golaem_node = NodegraphAPI.CreateNode('GolaemCache', ROOT_NODE)
    golaem_node.setName(node_name)
    golaem_node.getParameter('location').setValue('/root/world/geo/GolaemCache/' + node_name, 0)
    golaem_node.getParameter('crowdFields').setValue(crowd_fields, 0)
    golaem_node.getParameter('cacheName').setValue(cache_name, 0)
    golaem_node.getParameter('cacheFileDir').setValue(cache_dir, 0)
    golaem_node.getParameter('characterFiles').setValue(character_files, 0)
    golaem_node.getParameter('layout.enable').setValue(enable_layout, 0)
    if enable_layout:
        golaem_node.getParameter('layout.layoutFile').setValue(layout_file, 0)

    # get golaem node data
    golaem_node_name = golaem_node.getName()
    expression_value = "getNode('{0}').location + '/procedural'".format(golaem_node_name)

    # create GMS node
    gms_node = NodegraphAPI.CreateNode('GlmMasterSettings', ROOT_NODE)
    gms_node.getInputPort('i0').connect(golaem_node.getOutputPort('out'))
    gms_node.getParameter('user.GolaemProcedural').setExpression(expression_value, 2)

    try: 
        # set gms character file
        glmCharFileManager.delCharAll(gms_node, "master")
        glmCharFileManager.mkCharAssign(gms_node, "master")
    except:
        pass

    return golaem_node, gms_node


def glm_merge_node(node):
    merge = NodegraphAPI.CreateNode('Merge', ROOT_NODE)
    merge.setName('GlmMerge')
    merge.getParameter('showAdvancedOptions').setValue('Yes', 0)
    grp_attr = merge.getParameter('advanced.mergeGroupAttributes')
    grp_attr.resizeArray(1)
    grp_attr.getChildByIndex(0).setValue('lookfileMap', 0)

    node.getInputPort('i0').connect(merge.getOutputPort('out'))    
    node_pos = NodegraphAPI.GetNodePosition(node)    
    NodegraphAPI.SetNodePosition(merge, (node_pos[0], node_pos[1]+100))
    
    return merge


def get_align_x_pos(length):
    q, r = divmod(length, 2)

    if r == 0:
        x_pos = (q - 1) * 250 + 125
    else:
        x_pos = q * 250
    
    return -x_pos


def checking_golaem_data(golaem_node):
    global GOLAEM_MESSAGE
    
    node_name = golaem_node.getName()
    check_list = ['location', 'crowdFields', 'cacheName', 'cacheFileDir', 'characterFiles']
    
    for i in check_list:
        if not golaem_node.getParameter(i).getValue(0):
            GOLAEM_MESSAGE += '    {0}...{1} -> empty!!\n'.format(node_name, i)

    layout_enable = golaem_node.getParameter('layout.enable').getValue(0)
    layout_layoutfile = golaem_node.getParameter('layout.layoutFile').getValue(0)   
    if not layout_layoutfile and layout_enable == True:
        GOLAEM_MESSAGE += '    {0}...{1} -> warning!!\n'.format(node_name, 'layoutFile')    



def checking_gms_data(gms_node):
    global KLF_MESSAGE
    
    node_name = gms_node.getName()
    gcha_grp = gms_node.getParameter('user.CharacterFileManager.lookdevCharFiles')    
    material_grp = gms_node.getParameter('user.MaterialAssign')
    
    for g in gcha_grp.getChildren():
        if not g.getValue(0): 
            KLF_MESSAGE += '    {0}...{1} -> empty!!\n'.format(node_name, g.getName())

    for i in material_grp.getChildren():
        if 'LookfilePath' in i.getName():
            for j in i.getChildren():
                if 'LookfileMtlIn' in j.getName():
                    if not j.getValue(0):
                        KLF_MESSAGE += '    {0}...{1} -> empty!!\n'.format(node_name, j.getName())























