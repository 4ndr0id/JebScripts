# -*- coding: utf-8 -*-  
"""
Deobscure class name(use debug directives as source name) for PNF Software's JEB2.
"""
__author__ = 'Ericli'
'''
modified by 4ndr0id
'''

from com.pnfsoftware.jeb.client.api import IScript
from com.pnfsoftware.jeb.core import RuntimeProjectUtil
from com.pnfsoftware.jeb.core.units.code import ICodeUnit, ICodeItem
from com.pnfsoftware.jeb.core.units.code.android import IDexUnit
from com.pnfsoftware.jeb.core.actions import Actions, ActionContext, ActionCommentData, ActionRenameData
from java.lang import Runnable
import re
 
 
class JEB2DeobscureClass(IScript):
    def run(self, ctx):
        ctx.executeAsync("Running deobscure class ...", JEB2AutoRename(ctx))
        print('Done')
 
 
class JEB2AutoRename(Runnable):
    count = 0
    def __init__(self, ctx):
        self.ctx = ctx
 
    def run(self):
        ctx = self.ctx
        engctx = ctx.getEnginesContext()
        if not engctx:
            print('Back-end engines not initialized')
            return
        projects = engctx.getProjects()
        if not projects:
            print('There is no opened project')
            return
        prj = projects[0]
        units = RuntimeProjectUtil.findUnitsByType(prj, IDexUnit, False)
        for unit in units:
            classes = unit.getClasses()
            if classes:
                for clazz in classes:
                    sourceIndex = clazz.getSourceStringIndex()
                    clazzAddress = clazz.getAddress()
                    if sourceIndex == -1 or '$' in clazzAddress:# Do not rename inner class
                        continue
                    sourceStr = str(unit.getString(sourceIndex))
                    if '.java' in sourceStr:
                        sourceStr = sourceStr[:-5]
                    if clazz.getName(True) != sourceStr:
                        self.rename(unit, clazz, sourceStr, 'class')  # Rename class
                        fields = clazz.getFields()
                        if fields:
                            for field in fields:
                                nameIndex = field.getNameIndex()
                                if nameIndex ==-1:
                                    continue
                                classType = field.getFieldType().getAddress()
                                if '___' in classType:
                                    name = field.getName(True)
                                    if len(name) <= 3:   # 这里的判断是为了区分有意义的变量名和无意义的变量名
                                        classType = ((re.compile(r'[a-zA-Z]+')).findall(classType))[1]
                                        self.rename(unit, field, classType, 'field')    # Rename field
 
    def rename(self,unit,origin,source,flag):
        actCtx = ActionContext(unit, Actions.RENAME, origin.getItemId(), origin.getAddress())
        actData = ActionRenameData()
        if flag == 'field':
            newName = 'm%s_%d' % (source,self.count)
            self.count += 1
        else:
            newName = '%s___%s' % (source,origin.getName(True))
        actData.setNewName(newName)
        if unit.prepareExecution(actCtx, actData):
            try:
                result = unit.executeAction(actCtx, actData)
                if result:
                    print('rename to %s success!' % newName)
                else:
                    print('rename to %s failed!' % newName)
            except Exception, e:
                print (Exception, e)
