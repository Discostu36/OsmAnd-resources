#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import zlib

# =============================================================================
# =============================================================================
# =============================================================================

class OsmAndCoreResourcesPacker(object):
    # -------------------------------------------------------------------------
    def __init__(self):
        return

    # -------------------------------------------------------------------------
    def pack(self, resources, outputFilename):
        # Check if output directory exists
        outputDir = os.path.dirname(outputFilename)
        if not os.path.isdir(outputDir):
            os.makedirs(outputDir)

        # Open file for writing and and write header to it
        try:
            outputFile = open(outputFilename, "w")
        except IOError:
            print("Failed to open '%s' for writing" % (outputFilename))
            return False
        outputFile.write("// AUTOGENERATED FILE\n")
        outputFile.write("// Resources bundle for OsmAnd::CoreResourcesEmbeddedBundle\n")
        outputFile.write("\n")
        outputFile.write("#include <stddef.h>\n")
        outputFile.write("#include <stdint.h>\n")
        outputFile.write("\n")
        outputFile.write("#define ___STRINGIFY2(x) #x\n")
        outputFile.write("#define ___STRINGIFY(x) ___STRINGIFY2(x)\n")
        outputFile.write("\n")
        outputFile.write("#define GETTER_NAME(varname) __get__##varname\\\n")
        outputFile.write("\n")
        outputFile.write("#if defined(_WIN32) || defined(__CYGWIN__)\n")
        outputFile.write("#   define BUNDLE_API __declspec(dllexport)\n")
        outputFile.write("#elif (defined(__GNUC__) && __GNUC__ >= 4) || defined(__clang__)\n")
        outputFile.write("#   define BUNDLE_API __attribute__ ((visibility(\"default\"), used))\n")
        outputFile.write("#else\n")
        outputFile.write("#   define BUNDLE_API\n")
        outputFile.write("#endif\n")
        outputFile.write("\n")
        outputFile.write("#if defined(_MSC_VER)\n")
        outputFile.write("#   define EMIT_GETTER(varname, accessor)\\\n")
        outputFile.write("        __pragma( comment ( linker, \"/INCLUDE:_\"___STRINGIFY( __get__##varname ) ) )\\\n")
        outputFile.write("        BUNDLE_API const void* __get__##varname() {\\\n")
        outputFile.write("            return reinterpret_cast<const void*>(accessor varname);\\\n")
        outputFile.write("        }\n")
        outputFile.write("#else\n")
        outputFile.write("#   define EMIT_GETTER(varname, accessor)\\\n")
        outputFile.write("        BUNDLE_API const void* __get__##varname() {\\\n")
        outputFile.write("            return reinterpret_cast<const void*>(accessor varname);\\\n")
        outputFile.write("        }\n")
        outputFile.write("#endif // defined(_MSC_VER)\n")
        outputFile.write("\n")
        outputFile.write("extern \"C\" {\n")
        outputFile.write("\n")

        # For each resource in collection, pack it
        for (idx, resource) in enumerate(resources):
            if "hdpi" in resource[0]:
                continue
            originalSize = os.path.getsize(resource[0])
            with open(resource[0], "rb") as resourceFile:
                resourceContent = resourceFile.read()
                
            if not resource[0].endswith(".png"):
                packedContent = zlib.compress(resourceContent, 9)
            else:
                packedContent = resourceContent
            packedSize = len(packedContent)

            outputFile.write("static const char* const __CoreResourcesEmbeddedBundle__ResourceName_%d = \"%s\";\n" % (idx, resource[1]))
            outputFile.write("EMIT_GETTER(__CoreResourcesEmbeddedBundle__ResourceName_%d, )\n" % (idx))

            outputFile.write("static const uint8_t __CoreResourcesEmbeddedBundle__ResourceData_%d[] = {\n" % (idx))

            # Write size header
            outputFile.write("\t0x%02x, 0x%02x, 0x%02x, 0x%02x," % (
                (originalSize >> 24)&0xff,
                (originalSize >> 16)&0xff,
                (originalSize >>  8)&0xff,
                (originalSize >>  0)&0xff))

            # Write content
            for (byteIdx, byteValue) in enumerate(packedContent):
                if byteIdx % 16 == 0:
                    outputFile.write("\n\t")
                outputFile.write("0x%02x, " % (byteValue))
            outputFile.write("\n")
            outputFile.write("};\n")
            outputFile.write("EMIT_GETTER(__CoreResourcesEmbeddedBundle__ResourceData_%d, )\n" % (idx))

            outputFile.write("const size_t __CoreResourcesEmbeddedBundle__ResourceSize_%d = 4 + %d;\n" % (idx, packedSize))
            outputFile.write("EMIT_GETTER(__CoreResourcesEmbeddedBundle__ResourceSize_%d, &)\n" % (idx))
            outputFile.write("\n")

            print("Packed '%s'(%d bytes) as '%s'(4+%d bytes)..." % (resource[0], originalSize, resource[1], packedSize))

        # Write footer of the file and close it
        outputFile.write("const uint32_t __CoreResourcesEmbeddedBundle__ResourcesCount = %d;\n" % (len(resources)))
        outputFile.write("EMIT_GETTER(__CoreResourcesEmbeddedBundle__ResourcesCount, &)\n")
        outputFile.write("\n")
        outputFile.write("BUNDLE_API void __CoreResourcesEmbeddedBundle__FakeReferences() {\\\n")
        for (idx, resource) in enumerate(resources):
            outputFile.write("    GETTER_NAME(__CoreResourcesEmbeddedBundle__ResourceName_%d)();\n" % (idx))
            outputFile.write("    GETTER_NAME(__CoreResourcesEmbeddedBundle__ResourceData_%d)();\n" % (idx))
            outputFile.write("    GETTER_NAME(__CoreResourcesEmbeddedBundle__ResourceSize_%d)();\n" % (idx))
        outputFile.write("}\n")
        outputFile.write("\n")
        outputFile.write("} // extern \"C\"\n")
        outputFile.write("\n")
        outputFile.flush()
        outputFile.close()

        return True

# =============================================================================
# =============================================================================
# =============================================================================

if __name__=='__main__':
    # Get root directory of entire project
    rootPath = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    print("OsmAnd root path:      %s" % (rootPath))
    resourcesPath = rootPath + "/resources"
    print("OsmAnd resources path: %s" % (resourcesPath))

    # Output filename (in current working directory)
    workingDir = os.getcwd()
    if len(sys.argv) >= 2:
        workingDir = sys.argv[1]
    print("Working in: %s" % (workingDir))
    embeddedFilename = workingDir + "/gen/EmbeddedResourcesBundle.cpp"

    # Embedded resources
    with open(resourcesPath + "/embed-resources.list", "r") as embedResourcesListFile:
        embedResourcesList = embedResourcesListFile.readlines()
    embeddedResources = []
    for embedResourcesListEntry in embedResourcesList:
        embedResourcesListEntryParts = embedResourcesListEntry.split(':')
        originalPath = embedResourcesListEntryParts[0].strip()
        packedPath = embedResourcesListEntryParts[1].strip()
        embeddedResources.append((resourcesPath + originalPath, packedPath))

    packer = OsmAndCoreResourcesPacker()
    ok = packer.pack(embeddedResources, embeddedFilename)
    sys.exit(0 if ok else -1)
